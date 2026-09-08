#!/usr/bin/env python3
"""
A small standalone Superhero Story world about bacon, an unexpected twist,
and reconciliation after a rushed attempt to remove a problem.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "heroine", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "hero", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class City:
    name: str
    setting: str
    alarm: str = "the noon alarm"
    food: str = "bacon"
    danger: str = "a runaway kitchen cloud"


@dataclass
class StoryParams:
    hero: str
    partner: str
    city: str
    place: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    mission: str
    obstacle: str
    rushed_action: str
    consequence: str
    clue: str
    twist: str
    careful_action: str
    apology: str
    repair: str
    outcome: str
    lesson: str
    ending: str


HERO_NAMES = ["Luna", "Ruby", "Nova", "Pip", "Mara", "Zig"]
PARTNER_NAMES = ["Theo", "Bee", "Cora", "Finn", "Juno", "Max"]
CITIES = ["Brighton City", "Sunbeam City", "Maple City", "Cloud Harbor"]
PLACES = [
    "the rooftop market",
    "the city square",
    "the school kitchen",
    "the red-brick fire station",
    "the floating food fair",
]

TELLING_MODES = ["arrival", "warning", "dialogue", "countdown", "mystery", "promise"]

SCENARIOS = [
    Scenario(
        key="smoke_alarm",
        mission="was bringing a basket of bacon to the neighborhood breakfast",
        obstacle="a thick silver cloud curled around the market's alarm bell",
        rushed_action="used a gust of super-breath to remove the cloud",
        consequence="the cloud split into smaller puffs that covered every breakfast table",
        clue="the puffs smelled like bacon and drifted toward the sizzling griddle",
        twist="the cloud was harmless bacon steam trapped beneath a superhero-sized lid",
        careful_action="lifted the lid slowly while her partner opened the roof vents",
        apology="admitted that the first gust had scattered the steam",
        repair="guided the warm puffs into the vents and cleaned the bell together",
        outcome="the alarm rang clearly and the bacon breakfast could begin",
        lesson="a problem can look dangerous before we learn where it came from",
        ending="the clean bell chimed above the market while everyone shared crisp bacon",
    ),
    Scenario(
        key="flying_pan",
        mission="was guarding a community breakfast beside the old clock tower",
        obstacle="a giant frying pan flew in circles above the tower",
        rushed_action="tried to remove it with a glowing lasso",
        consequence="the pan spun faster and launched bacon into the sky",
        clue="the pan always turned when the tower clock made its softest tick",
        twist="the pan was part of a clockwork breakfast machine, not a villain's weapon",
        careful_action="matched the clock's rhythm and caught the pan when it slowed",
        apology="said the lasso had made the flying pan harder to control",
        repair="returned the pan to its gear and gathered every falling strip of bacon",
        outcome="the clock tower cooked breakfast for the whole block",
        lesson="careful listening can reveal the purpose of a strange object",
        ending="bacon fluttered onto plates as the clock struck twelve cheerful notes",
    ),
    Scenario(
        key="missing_sizzle",
        mission="was delivering bacon to a shelter before the evening meal",
        obstacle="the shelter's cooking sizzle had vanished completely",
        rushed_action="removed the quiet from the kitchen with a thunder clap",
        consequence="every pot rattled and the hungry children covered their ears",
        clue="a tiny sizzle still whispered inside one locked warming box",
        twist="the quiet was a sound shield protecting a shy robot cook",
        careful_action="knocked softly and asked the robot what kind of help it wanted",
        apology="apologized for making a loud rescue without asking first",
        repair="opened the box gently and helped the robot restart its bacon warmer",
        outcome="the kitchen filled with a friendly sizzle and a peaceful meal",
        lesson="help becomes kinder when the person affected gets a voice",
        ending="the robot cook served bacon in neat rows while the shelter grew warm",
    ),
    Scenario(
        key="bacon_beacon",
        mission="was carrying bacon to a rescue crew on Beacon Hill",
        obstacle="the hill's red beacon flashed a warning whenever the basket came near",
        rushed_action="tried to remove the flashing light with a magnetic glove",
        consequence="the beacon dimmed and a rescue boat lost its safe route",
        clue="the flashes matched the basket's metal handle",
        twist="the bacon basket had become the beacon's emergency signal key",
        careful_action="held the basket still and followed the beacon's three short flashes",
        apology="explained that the glove had nearly hidden the rescue signal",
        repair="returned the basket to its hook and reset the beacon's bright pattern",
        outcome="the rescue boat reached shore beneath a steady red light",
        lesson="an object may have an important job we cannot see at first",
        ending="the rescue crew shared the bacon beside the beacon's calm red glow",
    ),
    Scenario(
        key="grease_goblin",
        mission="was helping a friend prepare bacon sandwiches for a school fair",
        obstacle="a slippery grease goblin slid across the school roof",
        rushed_action="attempted to remove the goblin with a forceful cape-sweep",
        consequence="the goblin bounced into the kitchen and coated the sandwich table",
        clue="it stopped whenever someone offered it a clean napkin",
        twist="the goblin was a lonely crumb creature made from spilled breakfast grease",
        careful_action="offered it a cloth cape and showed it how to collect crumbs",
        apology="admitted that chasing it had made the mess spread",
        repair="washed the table and gave the goblin a safe little crumb bin",
        outcome="the goblin became the fair's helpful cleanup captain",
        lesson="understanding a nuisance can uncover a friend who needs a place",
        ending="the new cleanup captain waved a tiny cloth cape beside the bacon stand",
    ),
    Scenario(
        key="backward_bacon",
        mission="was taking bacon to a family picnic in the city park",
        obstacle="the picnic clock began running backward whenever bacon was placed on a plate",
        rushed_action="used super-speed to remove every strip from the picnic table",
        consequence="the guests forgot why they had gathered and the sandwiches fell apart",
        clue="the clock moved forward whenever two friends shared one piece",
        twist="the clock was measuring kindness, not minutes",
        careful_action="invited the guests to share the bacon and tell one thankful story",
        apology="said the hurried removal had interrupted the picnic's happiness",
        repair="rebuilt the plates and let everyone choose someone to thank",
        outcome="the clock ticked normally and the picnic continued",
        lesson="sharing can repair a day that force only makes confusing",
        ending="the clock hands moved forward as friends passed bacon beneath the trees",
    ),
]

WORLD_FACTS = {
    "food": "bacon",
    "action": "remove",
    "features": ["twist", "reconciliation"],
    "style": "superhero story",
}


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero Story world about bacon, removal, a twist, and reconciliation."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--partner", choices=PARTNER_NAMES)
    parser.add_argument("--city", choices=CITIES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    partner = args.partner or rng.choice([name for name in PARTNER_NAMES if name != hero])
    city = args.city or rng.choice(CITIES)
    place = args.place or rng.choice(PLACES)
    return StoryParams(
        hero=hero,
        partner=partner,
        city=city,
        place=place,
        seed=args.seed,
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    hero = params.hero
    partner = params.partner
    place = params.place
    mode = params.telling_mode or "arrival"
    if mode == "warning":
        return [
            f'"Something is spinning over {place}," {partner} warned.',
            f"Superhero {hero} landed beside {partner} while they {scenario.mission}.",
        ]
    if mode == "dialogue":
        return [
            f'"Ready for a peaceful breakfast rescue?" {hero} asked. "Only if there is bacon," {partner} replied.',
            f"They hurried to {place}, where they {scenario.mission}.",
        ]
    if mode == "countdown":
        return [
            f"The city clock counted down as Superhero {hero} raced toward {place}.",
            f"Before the last bell, {hero} and {partner} had to finish their mission: they {scenario.mission}.",
        ]
    if mode == "mystery":
        return [
            f"A strange smell drifted over {place}, and nobody could explain it.",
            f"Superhero {hero} followed the smell with {partner} while they {scenario.mission}.",
        ]
    if mode == "promise":
        return [
            f"{hero} had promised to protect the breakfast, so {hero} flew with {partner} to {place}.",
            f"They {scenario.mission}.",
        ]
    return [
        f"Superhero {hero} arrived at {place} with {partner} and a warm basket of bacon.",
        f"They {scenario.mission}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if not params.hero or not params.partner:
        raise StoryError("A hero and partner are required.")
    if params.hero == params.partner:
        raise StoryError("The hero and partner must have different names.")
    if params.scenario not in {scenario.key for scenario in SCENARIOS}:
        raise StoryError(f"Unknown scenario: {params.scenario}")

    rng = random.Random(params.seed)
    scenario = next(item for item in SCENARIOS if item.key == params.scenario)
    city = City(name=params.city, setting=params.place)
    world = World(city)

    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="hero",
            label="superhero",
            phrase=f"Superhero {params.hero}",
            location=params.place,
            meters={"courage": 1.0, "speed": 1.0},
            memes={"helpfulness": 1.0},
            traits=["brave", "quick"],
        )
    )
    partner = world.add(
        Entity(
            id=params.partner,
            kind="character",
            type="partner",
            label="partner",
            phrase=params.partner,
            location=params.place,
            meters={"care": 1.0, "patience": 1.0},
            memes={"trust": 1.0},
            traits=["observant", "honest"],
        )
    )
    bacon = world.add(
        Entity(
            id="bacon",
            kind="food",
            type="food",
            label="bacon",
            phrase="a basket of bacon",
            owner=params.hero,
            location=params.place,
            meters={"warmth": 1.0, "grease": 0.5},
            memes={"comfort": 1.0, "sharing": 0.5},
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="mystery",
            label="strange breakfast trouble",
            phrase="the strange breakfast trouble",
            location=params.place,
            meters={"danger": 0.7, "confusion": 1.0},
            memes={"mystery": 1.0},
        )
    )

    world.facts.update(
        hero=hero,
        partner=partner,
        bacon=bacon,
        obstacle=obstacle,
        scenario=scenario.key,
        mission=scenario.mission,
        twist=scenario.twist,
        reconciliation=scenario.repair,
        city=city.name,
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)
    world.say(
        rng.choice(
            [
                f"Then they discovered {scenario.obstacle}.",
                f"The peaceful mission changed when {scenario.obstacle}.",
                f"A sudden alarm revealed the trouble: {scenario.obstacle}.",
            ]
        )
    )

    world.para()
    world.say(
        rng.choice(
            [
                f'"I will remove it right away!" {hero.id} cried, and {hero.pronoun()} {scenario.rushed_action}.',
                f"{hero.id} saw danger and {scenario.rushed_action} before anyone could study it.",
                f'"Stand back!" {hero.id} shouted before {hero.pronoun()} {scenario.rushed_action}.',
            ]
        )
    )
    world.say(f"The rushed rescue caused a new problem: {scenario.consequence}.")
    world.say(
        rng.choice(
            [
                f'"Wait," {partner.id} said. "What do we actually know?"',
                f'{partner.id} raised a hand. "Let us look before we remove anything else."',
                f'"A superhero needs more than strong powers," {partner.id} reminded {hero.id}.',
            ]
        )
    )

    world.para()
    world.say(f"Together they watched carefully and noticed that {scenario.clue}.")
    world.say(f"That small clue led to a surprising twist: {scenario.twist}.")
    world.say(f"{hero.id} listened to {partner.id} and {scenario.careful_action}.")
    world.say(
        rng.choice(
            [
                f'"Now I understand," {hero.id} said. "The safest rescue is not always the fastest one."',
                f'{partner.id} smiled. "Knowing the truth helps us use our powers kindly."',
                f'"Thank you for stopping me," {hero.id} told {partner.id}.',
            ]
        )
    )

    world.para()
    world.say(f"{hero.id} {scenario.apology}.")
    world.say(
        rng.choice(
            [
                f'"I forgive you," {partner.id} answered. "Let us repair it together."',
                f'{partner.id} nodded. "An honest apology gives us a place to begin."',
                f'"We can fix this as a team," {partner.id} said.',
            ]
        )
    )
    world.say(f"Together they {scenario.repair}.")
    world.say(f"At last, {scenario.outcome}.")

    world.para()
    world.say(f"They carried one lesson home: {scenario.lesson}.")
    world.say(f"Their reconciliation made the whole rescue stronger.")
    world.say(f"By sunset, {scenario.ending}.")

    obstacle.location = "resolved"
    obstacle.meters["danger"] = 0.0
    obstacle.meters["confusion"] = 0.0
    obstacle.memes["understood"] = 1.0
    bacon.memes["sharing"] = 1.0
    hero.memes["reconciliation"] = 1.0
    partner.memes["forgiveness"] = 1.0
    world.facts.update(resolved=True, twist_revealed=True, reconciliation=True)

    prompts = [
        f"Write a child-friendly Superhero Story about {params.hero} and {params.partner}, including bacon and a problem they try to remove.",
        f"Tell a superhero tale with a surprising twist: {scenario.twist}. End with reconciliation.",
        f"Write a story set at {params.place} that shows this lesson: {scenario.lesson}.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.partner} discover?",
            answer=f"They discovered that {scenario.obstacle}. It interrupted their mission to {scenario.mission}.",
        ),
        QAItem(
            question="What happened when the hero tried to remove the problem too quickly?",
            answer=f"The rushed attempt caused trouble because {scenario.consequence}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {scenario.twist}. The clue that revealed it was that {scenario.clue}.",
        ),
        QAItem(
            question=f"How did {params.hero} and {params.partner} reconcile?",
            answer=f"{params.hero} apologized, and then they {scenario.repair}. Their shared repair restored trust.",
        ),
        QAItem(
            question="What lesson did the superheroes learn?",
            answer=f"They learned that {scenario.lesson}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="Why can removing something too quickly be risky?",
            answer="Removing something too quickly can make the problem worse because we may not understand its purpose.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters thought was true.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again by listening, apologizing, forgiving, and repairing the harm.",
        ),
        QAItem(
            question="Why is bacon useful in this storyworld?",
            answer="Bacon is a concrete shared food that gives the superheroes a reason to help, investigate, and celebrate together.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            details = []
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(details)}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("domain", "superhero"),
        asp.fact("ingredient", "bacon"),
        asp.fact("action", "remove"),
        asp.fact("feature", "twist"),
        asp.fact("feature", "reconciliation"),
        asp.fact("requires", "remove", "understanding"),
        asp.fact("requires", "reconciliation", "repair"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
understood :- requires(remove,understanding).
repaired :- requires(reconciliation,repair).
safe_rescue :- understood, repaired.
#show domain/1.
#show ingredient/1.
#show action/1.
#show feature/1.
#show understood/0.
#show repaired/0.
#show safe_rescue/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    features = sorted(asp.atoms(model, "feature"))
    expected_features = [("reconciliation",), ("twist",)]
    safe = bool(asp.atoms(model, "safe_rescue"))
    if features == expected_features and safe:
        print("OK: ASP and Python feature parity holds.")
        return 0
    print("MISMATCH: ASP parity failed.")
    print(f"features={features} safe_rescue={safe}")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show feature/1."))
        return
    if args.asp:
        import asp

        print(json.dumps([str(symbol) for symbol in asp.one_model(asp_program())], indent=2))
        return
    if args.verify:
        code = asp_verify()
        if code:
            raise SystemExit(code)
        test_params = StoryParams(
            hero="Luna",
            partner="Theo",
            city="Brighton City",
            place="the rooftop market",
            seed=77,
            scenario="smoke_alarm",
            telling_mode="dialogue",
        )
        sample = generate(test_params)
        required = ["bacon", "remove", "twist", "reconciliation"]
        if not all(word in (sample.story + " " + sample.story_qa[0].answer).lower() for word in required):
            print("MISMATCH: generated story lacks required narrative instruments.")
            raise SystemExit(1)
        print("OK: generated story exercised.")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Theo", "Brighton City", "the rooftop market", 101, "smoke_alarm", "arrival"),
            StoryParams("Ruby", "Bee", "Sunbeam City", "the city square", 202, "flying_pan", "dialogue"),
            StoryParams("Nova", "Cora", "Maple City", "the school kitchen", 303, "missing_sizzle", "mystery"),
            StoryParams("Mara", "Finn", "Cloud Harbor", "the red-brick fire station", 404, "bacon_beacon", "warning"),
            StoryParams("Pip", "Juno", "Brighton City", "the floating food fair", 505, "grease_goblin", "promise"),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            attempt += 1
            attempt_seed = base_seed + attempt
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
            sample = generate(params)
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
            params = sample.params
            header = f"### {params.hero} and {params.partner} in {params.city}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
