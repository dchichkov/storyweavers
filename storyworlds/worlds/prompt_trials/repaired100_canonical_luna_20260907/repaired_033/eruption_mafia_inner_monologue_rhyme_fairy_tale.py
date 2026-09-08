#!/usr/bin/env python3
"""
A standalone fairy-tale storyworld about a volcano, a lava-mafia, and a brave
inner voice that turns a dangerous eruption toward a safer ending.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


ENTITY_HUMAN = "human"
ENTITY_CREATURE = "creature"
ENTITY_OBJECT = "object"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    owner: Optional[str] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    fairy: str
    volcano: str
    mafia: str
    trial: str = "hidden_path"
    opening_style: int = 0
    rhyme_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    omen: str
    danger: str
    clue: str
    first_choice: str
    mafia_need: str
    brave_action: str
    invitation: str
    helper_action: str
    eruption_result: str
    ending: str
    lesson: str


SETTINGS = {
    "Moonlit Ember Valley": "Moonlit Ember Valley",
    "the Glass-Pine Kingdom": "the Glass-Pine Kingdom",
    "the Singing Crater": "the Singing Crater",
    "the Ashen Orchard": "the Ashen Orchard",
}

HERO_NAMES = ["Luna", "Mira", "Nell", "Orla", "Tessa", "Faye", "Elio"]
FAIRY_NAMES = ["Pip", "Brindle", "Mallow", "Tink", "Vela"]
VOLCANO_NAMES = ["Mount Sable", "Old Red Crown", "Emberpeak", "the Ruby Mountain"]
MAFIA_NAMES = ["the Cinder Circle", "the Ashen Mob", "the Lava League", "the Smoke Syndicate"]

TRIALS = {
    "hidden_path": Trial(
        omen="had promised to carry a moon-lantern to the castle before the volcano woke",
        danger="rolled black stones down the royal road and blocked every safe path",
        clue="noticed that the stones formed a crooked arrow toward a sealed cave",
        first_choice="tried to push one stone aside, but the ground shuddered and sent three more tumbling",
        mafia_need="was guarding a hidden tunnel where its youngest members were trapped by falling ash",
        brave_action="opened a small side passage with a silver shovel and marked the safe stones with blue chalk",
        invitation="You may use the marked path, but let us guide the eruption away from the village",
        helper_action="stacked glowing stones into a channel that turned the lava toward an empty basalt field",
        eruption_result="The eruption rushed like a red river, yet the village bridge stayed cool and whole",
        ending="At dawn, the moon-lantern still shone beside the new blue-chalk road.",
        lesson="Courage does not mean standing against danger alone; it means finding a wiser path through it.",
    ),
    "cinder_crown": Trial(
        omen="was bringing a lost crown to the queen when sparks began to fall",
        danger="demanded the crown as its price for stopping a smoky eruption",
        clue="saw tiny soot footprints leading from the volcano to a frightened dragon hatchling",
        first_choice="hid the crown beneath a cloak, but the sparks followed its shining edge",
        mafia_need="had promised the hatchling a bright crown because it feared the little dragon would be abandoned",
        brave_action="offered the crown's red ribbon and asked the queen to welcome the hatchling instead",
        invitation="Keep the ribbon for your friend, and help us protect the kingdom together",
        helper_action="wove the ribbon around a warning bell and rang it whenever a crack opened",
        eruption_result="The warning bell sounded before each burst, and every villager reached the stone shelter in time",
        ending="The crown rested on the queen's head while the dragon wore the ribbon like a sunrise.",
        lesson="A generous choice can reveal that what seems like a ransom is sometimes a plea for belonging.",
    ),
    "rhyme_bridge": Trial(
        omen="had to cross a singing bridge before the volcano's final bell",
        danger="sent smoky guards to collect a toll of one true secret from every traveler",
        clue="heard the guards whisper that they had forgotten the rhyme that kept the bridge awake",
        first_choice="offered a secret about a missing sock, but the bridge groaned and lowered one plank",
        mafia_need="was trying to remember the bridge song so its hidden family could escape the coming eruption",
        brave_action="shared an honest fear and built a new rhyme with the guards",
        invitation="Speak your worry, then rhyme with me; a truthful song may open the way",
        helper_action="beat a drum while the guards chanted the new verse and guided everyone across",
        eruption_result="The bridge lifted high as lava flashed below, carrying travelers safely to the far bank",
        ending="The volcano's roar became the bass line for a song nobody had known before.",
        lesson="Truth can be frightening, but shared truth can become a bridge.",
    ),
    "orchard_fire": Trial(
        omen="was tending the last silver apples before the mountain's red mouth opened",
        danger="sent hot ash over the orchard and claimed the trees as its secret garden",
        clue="found damp footprints around the roots where a hidden spring was being protected",
        first_choice="shouted at the ash-covered strangers, and they raised smoky shields",
        mafia_need="was protecting a spring that kept its families alive beneath the orchard",
        brave_action="dug a bright trench from the spring to the orchard wall and invited the villagers to help",
        invitation="Protect the spring with us, and let the water protect every tree",
        helper_action="guided the water into the trench while the villagers cleared fallen branches",
        eruption_result="Steam curled above the trench and softened the ash before it touched the silver apples",
        ending="The next morning, every apple wore a pearl of clean water.",
        lesson="Shared protection is stronger than a wall built by frightened neighbors.",
    ),
}

RHYME_LINES = [
    "When the red rocks rise, be wise before surprise.",
    "A listening heart can find a safer part.",
    "Name the fear, draw near, and make the pathway clear.",
    "A spark may start a fright, but care can guide the light.",
    "Speak what you know, and kinder rivers flow.",
    "The boldest knight knows when to seek a helping light.",
    "A secret kept alone can turn a pebble into stone.",
    "When friends unite, the darkest ash grows bright.",
]

OPENINGS = [
    "{hero} lived where the hills wore crowns of snow and the nights smelled of cinnamon smoke.",
    "Long ago, in a valley painted silver by the moon, there lived a thoughtful child named {hero}.",
    "At the edge of a fairy-tale kingdom stood a little house belonging to {hero}.",
    "The bells of {setting} knew {hero} as the child who listened before leaping.",
    "Every morning, {hero} watched the mountain and wondered what its deep rumble meant.",
    "In a kingdom where volcanoes slept beneath gardens, {hero} carried a lantern and a question.",
]


ASP_RULES = r"""
dangerous_eruption :- eruption(active), village(near), channel(unbuilt).
mafia_secret_need :- mafia(present), hidden_need(known).
safe_resolution :- eruption(active), channel(built), mafia_secret_need.
valid_story :- dangerous_eruption, safe_resolution.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("eruption", "active"),
            asp.fact("village", "near"),
            asp.fact("channel", "built"),
            asp.fact("mafia", "present"),
            asp.fact("hidden_need", "known"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program())
    return bool(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    if asp_valid():
        print("OK: ASP model confirms an active eruption can reach a safe resolution.")
        return 0
    print("MISMATCH: ASP model found no valid eruption resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale eruption and lava-mafia storyworld."
    )
    parser.add_argument("--setting", choices=list(SETTINGS))
    parser.add_argument("--hero")
    parser.add_argument("--fairy")
    parser.add_argument("--volcano")
    parser.add_argument("--mafia")
    parser.add_argument("--trial", choices=list(TRIALS))
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
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(HERO_NAMES),
        fairy=args.fairy or rng.choice(FAIRY_NAMES),
        volcano=args.volcano or rng.choice(VOLCANO_NAMES),
        mafia=args.mafia or rng.choice(MAFIA_NAMES),
        trial=args.trial or rng.choice(list(TRIALS)),
        opening_style=rng.randrange(len(OPENINGS)),
        rhyme_style=rng.randrange(len(RHYME_LINES)),
    )


def validate_params(params: StoryParams) -> None:
    names = [params.hero, params.fairy, params.volcano, params.mafia]
    if len({name.lower() for name in names}) != len(names):
        raise StoryError("The hero, fairy, volcano, and mafia need distinct names.")
    if not params.hero.strip():
        raise StoryError("The hero needs a readable name.")
    if not params.setting.strip():
        raise StoryError("The setting cannot be empty.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params.setting)
    hero = world.add(
        Entity(
            "hero",
            ENTITY_HUMAN,
            "child",
            params.hero,
            meters={"courage": 0.3, "safety": 0.0},
            memes={"worry": 0.2, "kindness": 0.0, "hope": 0.5},
            location="lantern house",
        )
    )
    fairy = world.add(
        Entity(
            "fairy",
            ENTITY_CREATURE,
            "fairy",
            params.fairy,
            meters={"magic": 1.0},
            memes={"trust": 0.4, "wonder": 0.8},
            location="lantern house",
        )
    )
    volcano = world.add(
        Entity(
            "volcano",
            ENTITY_OBJECT,
            "volcano",
            params.volcano,
            meters={"heat": 0.2, "pressure": 0.4, "eruption": 0.0},
            memes={"rumble": 0.5},
            location="mountain ridge",
        )
    )
    mafia = world.add(
        Entity(
            "mafia",
            ENTITY_CREATURE,
            "lava-mafia",
            params.mafia,
            meters={"smoke": 0.7, "danger": 0.7},
            memes={"fear": 0.8, "loyalty": 0.6, "shame": 0.0},
            location="sealed cave",
        )
    )
    world.add(
        Entity(
            "lantern",
            ENTITY_OBJECT,
            "moon-lantern",
            "moon-lantern",
            meters={"light": 1.0},
            owner="hero",
            location="lantern house",
        )
    )
    world.facts.update(
        params=params,
        trial=TRIALS[params.trial],
        hero=hero,
        fairy=fairy,
        volcano=volcano,
        mafia=mafia,
        clue_seen=False,
        need_understood=False,
        channel_built=False,
        eruption_started=False,
        resolved=False,
    )
    return world


def predict_safety(world: World) -> dict[str, bool]:
    sim = world.copy()
    volcano = sim.get("volcano")
    channel = sim.facts.get("channel_built", False)
    active = volcano.meters.get("eruption", 0.0) > 0.5
    return {"eruption_active": active, "village_safe": active and channel}


def act_opening(world: World) -> None:
    params = world.facts["params"]
    hero = world.get("hero")
    fairy = world.get("fairy")
    volcano = world.get("volcano")
    trial = world.facts["trial"]
    world.say(
        OPENINGS[params.opening_style].format(
            hero=hero.label,
            setting=world.setting,
        )
    )
    world.say(
        f"{hero.label} tended the moon-lantern with {fairy.label}, while "
        f"{volcano.label} slept beyond the valley and {trial.omen}."
    )
    world.say(
        f"Inside {hero.label}'s thoughts, a small voice whispered, "
        f"“A rumble is a warning, not a command. Listen, then plan.”"
    )


def act_eruption(world: World) -> None:
    hero = world.get("hero")
    volcano = world.get("volcano")
    mafia = world.get("mafia")
    trial = world.facts["trial"]
    volcano.meters["pressure"] = 1.0
    volcano.meters["heat"] = 1.0
    volcano.meters["eruption"] = 1.0
    mafia.meters["danger"] = 1.0
    world.facts["eruption_started"] = True
    world.say(
        f"Then {volcano.label} woke with a thunderous {trial.danger}. "
        f"The {mafia.label} appeared through the smoke, wearing ember-red scarves."
    )
    world.say(
        f"{hero.label}'s knees trembled. “If I run without thinking, the road may trap us,” "
        f"{hero.label} said aloud. The inner voice answered, “Fear can ring a bell; let it ring.”"
    )
    world.say(trial.omen.split(" had ")[0] + " had never seen such a red sky.")
    world.say(RHYME_LINES[world.facts["params"].rhyme_style])


def act_clue(world: World) -> None:
    hero = world.get("hero")
    fairy = world.get("fairy")
    mafia = world.get("mafia")
    trial = world.facts["trial"]
    world.facts["clue_seen"] = True
    world.say(
        f"{hero.label} watched instead of shouting. {hero.label} {trial.clue}. "
        f"{fairy.label} sprinkled moon-dust over the marks, making the hidden arrow shine."
    )
    world.say(
        f"“You are not stealing the valley,” {hero.label} called to the {mafia.label}. "
        f"“You are trying to protect someone.”"
    )
    world.say(
        f"The tallest smoky guard bowed. “We are a mafia of lava, perhaps, but "
        f"{trial.mafia_need},” it confessed."
    )
    world.facts["need_understood"] = True
    world.get("mafia").memes["shame"] = 0.2
    world.get("mafia").memes["fear"] = 0.5


def act_choice(world: World) -> None:
    hero = world.get("hero")
    mafia = world.get("mafia")
    trial = world.facts["trial"]
    world.say(f"First, {hero.label} {trial.first_choice}.")
    world.say(
        f"“A brave heart is not a hard heart,” {hero.label} thought. "
        f"“If their fear has made trouble, kindness must still repair the trouble.”"
    )
    world.say(
        f"{hero.label} faced the {mafia.label}. “Help me build a safer answer,” "
        f"{hero.label} said. “Your secret need matters, and so does everyone in the valley.”"
    )
    world.say(f"The smoky guards answered, “Show us where to stand, and we will stand there.”")


def act_solution(world: World) -> None:
    hero = world.get("hero")
    fairy = world.get("fairy")
    mafia = world.get("mafia")
    volcano = world.get("volcano")
    trial = world.facts["trial"]
    world.say(
        f"{hero.label} {trial.brave_action}. {fairy.label} lifted a silver wand, "
        f"and the {mafia.label} moved stones with careful, glowing hands."
    )
    world.say(f"{hero.label} told them, “{trial.invitation}”")
    world.say(f"The mafia replied, “Then let our secret work become a public rescue.”")
    world.say(f"The {mafia.label} {trial.helper_action}.")
    world.facts["channel_built"] = True
    hero.meters["courage"] = 1.0
    hero.meters["safety"] = 1.0
    hero.memes["kindness"] = 1.0
    mafia.meters["danger"] = 0.2
    mafia.memes["loyalty"] = 1.0


def act_resolution(world: World) -> None:
    hero = world.get("hero")
    fairy = world.get("fairy")
    volcano = world.get("volcano")
    mafia = world.get("mafia")
    trial = world.facts["trial"]
    world.say(
        f"At last, {trial.eruption_result}. The eruption still roared, but its "
        f"wild red river now followed the channel made by many careful hands."
    )
    world.say(
        f"{volcano.label} cooled from angry red to warm gold. {fairy.label} rang the "
        f"moon-lantern, and {hero.label} saw the {mafia.label} open the cave for every family inside."
    )
    world.say(trial.ending)
    world.say(f"“{trial.lesson}” {hero.label} said, and the valley agreed.")
    world.say(RHYME_LINES[(world.facts["params"].rhyme_style + 3) % len(RHYME_LINES)])
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_opening(world)
    world.para()
    act_eruption(world)
    act_clue(world)
    act_choice(world)
    act_solution(world)
    world.para()
    act_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    trial = world.facts["trial"]
    return [
        f"Write a child-friendly fairy tale about an eruption in {world.setting}.",
        f"Include {params.hero}, a fairy named {params.fairy}, and {params.mafia}, a lava-mafia with a hidden need.",
        f"Use inner monologue and rhyme as {params.hero} turns danger into cooperation: {trial.lesson}",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    fairy = world.get("fairy")
    volcano = world.get("volcano")
    mafia = world.get("mafia")
    trial = world.facts["trial"]
    return [
        QAItem(
            question=f"What danger began the story for {hero.label}?",
            answer=f"{volcano.label} woke with an eruption that {trial.danger}.",
        ),
        QAItem(
            question=f"What did {hero.label} discover about {mafia.label}?",
            answer=f"{hero.label} discovered that {mafia.label} {trial.mafia_need}.",
        ),
        QAItem(
            question=f"How did the inner monologue help {hero.label}?",
            answer="The inner voice helped the hero pause, understand the danger, and choose a careful plan instead of running blindly.",
        ),
        QAItem(
            question=f"What did {hero.label} say to the lava-mafia?",
            answer=f"{hero.label} invited them to help build a safer answer: “{trial.invitation}”",
        ),
        QAItem(
            question="How was the eruption made safer?",
            answer=f"The lava-mafia {trial.helper_action}, guiding the eruption toward a safer route.",
        ),
        QAItem(
            question="What proved that the problem was resolved?",
            answer=f"{trial.ending} The volcano cooled, and the hidden families were safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an eruption?",
            answer="An eruption is when a volcano releases hot lava, ash, gas, or rocks.",
        ),
        QAItem(
            question="What is a volcano?",
            answer="A volcano is an opening or mountain through which melted rock and gases can rise from inside Earth.",
        ),
        QAItem(
            question="What does mafia mean in this story world?",
            answer="Here, the mafia is a fictional group of smoky lava creatures. They are dangerous when frightened, but they can choose cooperation and repair harm.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the character's private thinking, shown as thoughts inside the story.",
        ),
        QAItem(
            question="Why does the story use rhyme?",
            answer="The rhyme gives the fairy tale a memorable, musical voice while reminding the characters of its wisdom.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.label} ({entity.type}) "
            f"location={entity.location} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


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
    StoryParams(
        setting="Moonlit Ember Valley",
        hero="Luna",
        fairy="Pip",
        volcano="Mount Sable",
        mafia="the Cinder Circle",
        trial="hidden_path",
        opening_style=1,
        rhyme_style=0,
    ),
    StoryParams(
        setting="the Glass-Pine Kingdom",
        hero="Mira",
        fairy="Brindle",
        volcano="Emberpeak",
        mafia="the Ashen Mob",
        trial="cinder_crown",
        opening_style=2,
        rhyme_style=2,
    ),
    StoryParams(
        setting="the Singing Crater",
        hero="Nell",
        fairy="Mallow",
        volcano="Old Red Crown",
        mafia="the Smoke Syndicate",
        trial="rhyme_bridge",
        opening_style=3,
        rhyme_style=4,
    ),
    StoryParams(
        setting="the Ashen Orchard",
        hero="Orla",
        fairy="Vela",
        volcano="the Ruby Mountain",
        mafia="the Lava League",
        trial="orchard_fire",
        opening_style=5,
        rhyme_style=6,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP story model:")
        print("  valid_story")
        print(f"  solved: {'yes' if asp_valid() else 'no'}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise StoryError("The number of stories must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 40):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not create enough distinct story variants.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.hero} / {params.volcano} / {params.mafia}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
