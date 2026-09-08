#!/usr/bin/env python3
"""
A standalone storyworld about a precocious child, a humming dryer, and a sword
that becomes useful only through friendship.
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
ENTITY_OBJECT = "object"
ENTITY_MACHINE = "machine"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

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
    friend: str
    dryer: str
    sword: str
    scenario: str = "storm"
    opening_style: int = 0
    hero_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    danger: str
    clue: str
    first_try: str
    need: str
    friendship_action: str
    invitation: str
    helpful_action: str
    rescue: str
    ending: str
    lesson: str


SETTINGS = {
    "laundry_room": "the bright laundry room",
    "clubhouse": "the neighborhood clubhouse",
    "school_basement": "the school basement",
    "apartment_hall": "the apartment hall",
}

HERO_NAMES = ["Luna", "Mara", "Pip", "Nell", "Tavi", "Rae"]
FRIEND_NAMES = ["Jo", "Bea", "Milo", "Kit", "Sam", "Ari"]
DRYER_NAMES = ["Rumble", "Whirly", "Tumble", "Breezy"]
SWORD_NAMES = ["Brightedge", "Starblade", "Kindsteel", "Sunflash"]

SCENARIOS = {
    "storm": Scenario(
        danger="a sudden storm knocked out the lights while a frightened kitten cried from behind the warm dryer",
        clue="heard the dryer thump in a steady pattern instead of making its usual rumble",
        first_try="raised the sword and shouted a heroic command, but the echo only made the kitten hide deeper",
        need="was tapping a message about the trapped kitten and the safest way to reach it",
        friendship_action="lowered the sword, listened beside the dryer, and asked the friend to help read the rhythm",
        invitation="We can be heroes together. You tap, I listen, and the sword will make light only when we need it",
        helpful_action="tapped three short beats while the sword reflected a thin stripe of moonlight under the dryer",
        rescue="followed the reflected stripe and guided the kitten toward a basket instead of pulling it into the dark",
        ending="When the power returned, the dryer gave one proud warm puff, and the kitten curled between the two friends like a tiny cape",
        lesson="Friendship makes courage wiser because good heroes listen before they act.",
    ),
    "sock_goblin": Scenario(
        danger="a mountain of warm socks slid from the dryer and hid the clubhouse emergency key",
        clue="noticed the dryer was stopping after every fourth tumble, as if something small blocked its door",
        first_try="used the sword to poke the sock mountain, which only launched a woolly sock onto the ceiling fan",
        need="was trying to point out a trapped toy goblin that had borrowed the key as a pretend treasure",
        friendship_action="asked the friend to make a calm treasure map while the sword stayed safely on the table",
        invitation="You know the map, I know the safe way to open the pile, and neither of us has to guess alone",
        helpful_action="held the map while the sword's blunt side lifted one sock at a time",
        rescue="found the key and let the toy goblin keep a button as its new treasure",
        ending="The dryer began to spin again, and the emergency key gleamed beside a perfectly paired sock",
        lesson="Friends turn a messy problem into shared work instead of a contest.",
    ),
    "moonlight": Scenario(
        danger="the dryer window flashed with a strange blue glow that made everyone think a space villain had landed",
        clue="saw the glow repeat whenever the drum turned past one loose silver ribbon",
        first_try="pointed the sword at the window and announced a challenge to the invisible villain",
        need="was trying to warn that the ribbon could catch and tear if the dryer kept spinning",
        friendship_action="let the friend explain the pattern and used the sword only as a hook after unplugging the machine",
        invitation="Tell me what you see, and I will use my superhero tool carefully",
        helpful_action="hooked the loose ribbon with the sword's guard while the friend held a flashlight",
        rescue="removed the ribbon before it tangled and turned the blue glow into a harmless reflection",
        ending="The dryer window showed two smiling faces and one sword shining like a friendly crescent moon",
        lesson="A clever friend can spot the truth behind a frightening mystery.",
    ),
    "lost_signal": Scenario(
        danger="the building's rescue beacon stopped blinking, leaving a lost delivery robot outside in the rain",
        clue="heard the dryer beep in the same three-note pattern as the beacon's missing signal",
        first_try="swung the sword toward the ceiling, hoping its shine would summon help, but it only startled a pigeon",
        need="was copying the beacon signal so the robot could find the warm doorway",
        friendship_action="stood beside the friend and matched the beeps instead of trying to be the only hero",
        invitation="You copy the signal, I will keep the doorway clear, and the sword can point the way",
        helpful_action="used the sword to reflect three bright flashes while the friend repeated the dryer beeps",
        rescue="guided the robot from the rain to the dry hall",
        ending="The robot delivered one warm towel, which became the team's first official superhero cape",
        lesson="Friendship sends help farther than one loud voice can reach.",
    ),
    "dragon_shirt": Scenario(
        danger="a red shirt came out of the dryer looking like a tiny dragon and frightened the youngest club members",
        clue="noticed the shirt's pocket was puffed around a toy dragon that was making its wings flap",
        first_try="held the sword in front of the shirt, but the toy dragon puffed even harder",
        need="was trying to escape the hot pocket before the dryer began another cycle",
        friendship_action="asked the friend to sing a gentle marching song while carefully cooling the shirt",
        invitation="Your song can make it brave; my sword can lift the pocket only when you say ready",
        helpful_action="waited for the friend's signal, then used the sword's flat side to open the pocket",
        rescue="freed the toy dragon and folded the shirt into a safe little nest",
        ending="The pretend dragon rested in the nest while the dryer hummed a soft victory tune",
        lesson="Bravery grows when friends make room for one another's special skills.",
    ),
    "hero_badge": Scenario(
        danger="the dryer swallowed a cardboard superhero badge just before the friendship parade",
        clue="found a tiny corner of the badge peeking through the lint screen",
        first_try="promised to slice the screen open with the sword, but the friend wisely stepped between the blade and the machine",
        need="was protecting the dryer from damage while trying to save the badge",
        friendship_action="thanked the friend for stopping the dangerous idea and worked through the safe instructions together",
        invitation="You were right to stop me. Show me the safe latch, and I will hold the light",
        helpful_action="held the sword's lantern-like reflection on the latch while the friend opened it",
        rescue="retrieved the badge without harming the screen",
        ending="The badge was wrinkled, but both friends wore it together by fastening it to a shared ribbon",
        lesson="A true superhero accepts a friend's warning and changes course.",
    ),
}

OPENINGS = [
    "{hero} loved two things: inventing superhero plans and making sure every friend got home safely.",
    "In {setting}, {hero} wore a towel as a cape and took every small problem very seriously.",
    "{hero} was precocious enough to make a rescue chart before breakfast, but still young enough to trip over the cape.",
    "Everyone in {setting} knew {hero} had a big imagination and an even bigger wish to help.",
    "{hero} had declared the laundry room a superhero headquarters, complete with a humming dryer and a shiny sword.",
    "Some heroes had secret lairs. {hero} had {setting}, a brave friend, and a dryer that never kept quiet.",
]

HERO_STYLES = [
    "stood tall, though the towel cape slipped over one eye",
    "checked the rescue plan twice and then checked whether the cape was on backward",
    "tried to look serious while one sock clung to a boot",
    "raised a fist, then remembered that careful hands were part of being heroic",
    "announced the plan in a grand voice that made the dryer wobble with laughter",
    "took one deep breath and left room for the friend to speak",
]

ASP_RULES = r"""
% The machine creates a problem when it is active and the danger is unresolved.
dangerous(S) :- setting(S), dryer_active(dryer), trouble(unresolved).

% Friendship makes a safe plan possible.
safe_plan(S) :- setting(S), friendship(hero,friend), listens(hero), helper(friend).

% A complete superhero story requires the safe plan and a changed sword.
valid_story(S) :- dangerous(S), safe_plan(S), sword_repurposed(sword), rescued(friend).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("setting", key) for key in SETTINGS]
    lines.extend(
        [
            asp.fact("dryer_active", "dryer"),
            asp.fact("trouble", "unresolved"),
            asp.fact("friendship", "hero", "friend"),
            asp.fact("listens", "hero"),
            asp.fact("helper", "friend"),
            asp.fact("sword_repurposed", "sword"),
            asp.fact("rescued", "friend"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(SETTINGS)
    actual = {setting for (setting,) in asp_valid()}
    if expected == actual:
        print(f"OK: ASP model covers {len(expected)} story settings.")
        return 0
    print("MISMATCH between Python and ASP setting coverage.")
    print("only python:", sorted(expected - actual))
    print("only asp:", sorted(actual - expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A dryer, precocious child, sword, and friendship superhero storyworld."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--dryer")
    parser.add_argument("--sword")
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
        friend=args.friend or rng.choice(FRIEND_NAMES),
        dryer=args.dryer or rng.choice(DRYER_NAMES),
        sword=args.sword or rng.choice(SWORD_NAMES),
        scenario=rng.choice(list(SCENARIOS)),
        opening_style=rng.randrange(len(OPENINGS)),
        hero_style=rng.randrange(len(HERO_STYLES)),
    )


def validate_params(params: StoryParams) -> None:
    if params.hero.lower() == params.friend.lower():
        raise StoryError("The hero and friend need different names.")
    if params.hero.lower() == params.dryer.lower():
        raise StoryError("The dryer needs a different name from the hero.")
    if params.friend.lower() == params.dryer.lower():
        raise StoryError("The dryer needs a different name from the friend.")
    if not params.hero.strip() or not params.friend.strip():
        raise StoryError("The hero and friend need readable names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(SETTINGS[params.setting])

    hero = world.add(
        Entity(
            id="hero",
            kind=ENTITY_HUMAN,
            type="precocious_child",
            label=params.hero,
            phrase=f"the precocious hero {params.hero}",
            meters={"courage": 1.0, "care": 0.0},
            memes={"confidence": 1.0, "friendship": 0.0, "worry": 0.0},
            location=world.setting,
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind=ENTITY_HUMAN,
            type="friend",
            label=params.friend,
            phrase=f"{params.friend}, {params.hero}'s friend",
            meters={"helpfulness": 1.0, "safety": 1.0},
            memes={"trust": 1.0, "friendship": 1.0},
            location=world.setting,
        )
    )
    dryer = world.add(
        Entity(
            id="dryer",
            kind=ENTITY_MACHINE,
            type="dryer",
            label=params.dryer,
            phrase=f"the dryer called {params.dryer}",
            meters={"warmth": 1.0, "motion": 1.0, "danger": 1.0},
            memes={"mystery": 1.0},
            location=world.setting,
        )
    )
    sword = world.add(
        Entity(
            id="sword",
            kind=ENTITY_OBJECT,
            type="practice_sword",
            label=params.sword,
            phrase=f"the practice sword {params.sword}",
            meters={"sharpness": 0.0, "brightness": 1.0, "usefulness": 0.0},
            memes={"pride": 1.0, "patience": 0.0},
            owner=hero.id,
            location=world.setting,
        )
    )

    world.facts.update(
        params=params,
        scenario=SCENARIOS[params.scenario],
        hero=hero,
        friend=friend,
        dryer=dryer,
        sword=sword,
        danger_seen=False,
        clue_understood=False,
        friendship_active=False,
        sword_repurposed=False,
        rescued=False,
    )
    return world


def predict(world: World) -> dict[str, bool]:
    sim = world.copy()
    dryer = sim.get("dryer")
    sword = sim.get("sword")
    return {
        "danger": dryer.meters.get("danger", 0.0) > 0.0,
        "safe_sword": sword.meters.get("usefulness", 0.0) > 0.0,
    }


def act_opening(world: World) -> None:
    params = world.facts["params"]
    world.say(
        OPENINGS[params.opening_style].format(
            hero=params.hero,
            setting=world.setting,
        )
    )
    world.say(
        f"{params.hero} had recruited {params.friend} for the day's superhero patrol, "
        f"and the dryer called {params.dryer} was their headquarters."
    )


def act_danger(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    dryer = world.get("dryer")
    sword = world.get("sword")
    scenario = world.facts["scenario"]
    params = world.facts["params"]

    world.facts["danger_seen"] = True
    hero.memes["worry"] = 1.0
    dryer.meters["danger"] = 1.0
    dryer.meters["motion"] = 0.0
    world.say(f"Then trouble arrived: {scenario.danger}.")
    world.say(f"{params.hero} {HERO_STYLES[params.hero_style]} and grabbed {sword.phrase}.")
    world.say(f"{params.hero} tried a first rescue: {scenario.first_try}.")
    world.say(f'"Wait," said {friend.label}. "The dryer is telling us something."')


def act_listening(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    dryer = world.get("dryer")
    scenario = world.facts["scenario"]

    hero.meters["care"] = 1.0
    hero.memes["friendship"] = 1.0
    friend.memes["trust"] = 2.0
    dryer.memes["mystery"] = 0.0
    world.facts["clue_understood"] = True
    world.facts["friendship_active"] = True

    world.say(f"{hero.label} listened instead of charging ahead. {scenario.clue}.")
    world.say(f"The pattern explained that {scenario.need}.")
    world.say(f'"You noticed what I missed," {hero.label} told {friend.label}.')
    world.say(f'"That is what friends are for," {friend.label} replied.')
    world.say(f"{hero.label} {scenario.friendship_action}.")
    world.say(f'"{scenario.invitation}," said {hero.label}.')


def act_team_rescue(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    dryer = world.get("dryer")
    sword = world.get("sword")
    scenario = world.facts["scenario"]

    dryer.meters["danger"] = 0.0
    dryer.meters["motion"] = 0.0
    sword.meters["usefulness"] = 1.0
    sword.meters["brightness"] = 2.0
    sword.memes["patience"] = 1.0
    world.facts["sword_repurposed"] = True
    world.facts["rescued"] = True
    friend.meters["safety"] = 2.0

    world.say(f"{friend.label} nodded, and {scenario.helpful_action}.")
    world.say(f"Together, {hero.label} and {friend.label} {scenario.rescue}.")
    world.say(
        f"The sword was still shiny, but its best power was no longer pretending to be dangerous; "
        f"it had become a careful tool in a friendship rescue."
    )


def act_ending(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    dryer = world.get("dryer")
    scenario = world.facts["scenario"]

    hero.memes["confidence"] = 2.0
    hero.memes["worry"] = 0.0
    dryer.meters["warmth"] = 2.0
    world.say(f"{hero.label} and {friend.label} shared a relieved superhero high-five. {scenario.ending}.")
    world.say(scenario.lesson)
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_opening(world)
    world.para()
    act_danger(world)
    act_listening(world)
    act_team_rescue(world)
    world.para()
    act_ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a child-friendly superhero story about {params.hero}, a precocious child, in {world.setting}.",
        f"Include the dryer called {params.dryer}, the sword {params.sword}, and a friendship with {params.friend}.",
        f"Show how listening changes the rescue when {scenario.danger}.",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            question=f"What kind of hero was {params.hero}?",
            answer=f"{params.hero} was a precocious hero who wanted to help quickly but learned to listen carefully.",
        ),
        QAItem(
            question=f"What trouble happened with the dryer called {params.dryer}?",
            answer=f"{scenario.danger.capitalize()}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} understand the trouble?",
            answer=f"{params.hero} noticed that {scenario.clue}.",
        ),
        QAItem(
            question=f"How did {params.friend} help?",
            answer=f"{params.friend} helped by noticing the message, sharing a safe plan, and working together with {params.hero}.",
        ),
        QAItem(
            question=f"How was the sword {params.sword} used?",
            answer=f"The sword was used carefully as a helpful tool, not as a weapon: {scenario.helpful_action}.",
        ),
        QAItem(
            question="What did friendship change?",
            answer=f"Friendship changed the rescue from a reckless solo attempt into a careful team effort, and {scenario.rescue}.",
        ),
        QAItem(
            question="What proved that the problem was solved?",
            answer=f"The ending showed that {scenario.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dryer?",
            answer="A dryer is a machine that uses moving air and warmth to remove water from clothes.",
        ),
        QAItem(
            question="What does precocious mean?",
            answer="Precocious means showing unusually advanced cleverness or understanding for one's age.",
        ),
        QAItem(
            question="What is a sword in this storyworld?",
            answer="The sword is a safe practice sword used as a symbol and a careful tool, not for hurting people.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring connection in which people listen, trust one another, and help each other.",
        ),
        QAItem(
            question="What makes a superhero choice wise?",
            answer="A wise superhero choice protects others, listens for clues, and uses tools carefully instead of rushing into danger.",
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
            f"meters={entity.meters} memes={entity.memes} location={entity.location}"
        )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
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
        setting="laundry_room",
        hero="Luna",
        friend="Jo",
        dryer="Rumble",
        sword="Starblade",
        scenario="storm",
    ),
    StoryParams(
        setting="clubhouse",
        hero="Mara",
        friend="Bea",
        dryer="Tumble",
        sword="Kindsteel",
        scenario="sock_goblin",
    ),
    StoryParams(
        setting="school_basement",
        hero="Pip",
        friend="Milo",
        dryer="Whirly",
        sword="Brightedge",
        scenario="moonlight",
    ),
    StoryParams(
        setting="apartment_hall",
        hero="Nell",
        friend="Ari",
        dryer="Breezy",
        sword="Sunflash",
        scenario="lost_signal",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("Compatible ASP story settings:")
        for setting, in asp_valid():
            print(f"  {setting}")
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
        while len(samples) < args.n and attempt < max(50, args.n * 30):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if len(samples) < args.n:
            raise StoryError("Could not generate the requested number of distinct stories.")

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
            header = (
                f"### {params.hero} / {params.friend} / "
                f"{params.dryer} / {params.sword} in {params.setting}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
