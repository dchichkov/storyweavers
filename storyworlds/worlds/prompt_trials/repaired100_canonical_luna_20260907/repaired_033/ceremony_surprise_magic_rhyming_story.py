#!/usr/bin/env python3
"""
A standalone storyworld for a rhyming ceremony with a magical surprise.
"""

from __future__ import annotations

import argparse
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
ENTITY_MAGIC = "magic"


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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    setting: str
    hero: str
    guest: str
    token: str
    ceremony: str = "lantern"
    verse_style: int = 0
    surprise_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class CeremonyPlan:
    purpose: str
    trouble: str
    clue: str
    first_try: str
    hidden_need: str
    magic_action: str
    invitation: str
    helper_action: str
    reveal: str
    ending: str
    lesson: str


SETTINGS = {
    "moonlit courtyard": "the moonlit courtyard",
    "village green": "the village green",
    "hilltop garden": "the hilltop garden",
    "river meadow": "the river meadow",
}

HERO_NAMES = ["Luna", "Mira", "Nell", "Pip", "Tessa", "Willa"]
GUEST_NAMES = ["Bram", "Clover", "Dew", "Finn", "Moss", "Robin"]
TOKENS = ["silver bell", "blue ribbon", "golden leaf", "glowing pebble", "star-shaped key"]

CEREMONIES = {
    "lantern": CeremonyPlan(
        purpose="welcome the first evening star with a gentle lantern ceremony",
        trouble="the welcome lanterns all went dark just before the guests arrived",
        clue="noticed a tiny blue glow moving beneath the old stone table",
        first_try="struck a match, but the sudden spark made the little glow dart away",
        hidden_need="was hiding because the ceremony's bright lights had frightened it",
        magic_action="lifted the lanterns high and softened their flames with a moon-silk spell",
        invitation="You may join our ceremony in the gentlest light",
        helper_action="floated from lantern to lantern, lighting each one with a quiet blue spark",
        reveal="the guest had been a shy star-sprite carrying the missing evening light",
        ending="When the final lantern shone, the star-sprite bowed, and the whole courtyard twinkled like a sky turned upside down.",
        lesson="A welcoming ceremony becomes magical when it makes room for the timid.",
    ),
    "ribbon": CeremonyPlan(
        purpose="tie a ribbon of thanks around the oldest apple tree",
        trouble="the ribbon flew loose and tangled around every branch",
        clue="heard a soft giggle each time the ribbon curled toward the highest twig",
        first_try="pulled the ribbon down, but the knot only grew into a woolly red cloud",
        hidden_need="was playing a wind game and did not know the tree was part of the ceremony",
        magic_action="whispered a rhyme that turned the ribbon into a slow, shining spiral",
        invitation="Dance with us, then rest your ribbon on the tree",
        helper_action="guided the spiral around the trunk and tied one neat bow",
        reveal="the playful breeze itself had become a tiny invisible guest",
        ending="The bow bobbed in the breeze, and every apple seemed to clap with a rosy cheek.",
        lesson="Clear invitations can turn wild play into a welcome part of a celebration.",
    ),
    "bell": CeremonyPlan(
        purpose="ring a little bell to thank helpers after the harvest",
        trouble="the bell vanished from the cushion where it had been polished",
        clue="found bright footprints leading toward a basket of sleepy seeds",
        first_try="searched under every cloth, but the bell gave one teasing ring from somewhere above",
        hidden_need="was waking the seeds because the cold night might bury them too deeply",
        magic_action="sang a warm rhyme that made the bell ring without startling the seeds",
        invitation="Ring softly with us, and the seeds can dream in peace",
        helper_action="tapped the bell in a gentle rhythm until the seeds settled safely",
        reveal="the missing ringer was a seed-keeper no taller than a thimble",
        ending="The bell chimed once, the seeds snuggled down, and a green shoot peeked up to listen.",
        lesson="Magic is kindest when its music protects small growing things.",
    ),
    "crown": CeremonyPlan(
        purpose="place a flower crown on the guest of honor",
        trouble="the crown rose into the air and spun away whenever anyone reached for it",
        clue="saw a trail of pollen arrows pointing toward the quietest corner",
        first_try="jumped for the crown, but it bounced higher with every jump",
        hidden_need="was carrying flower pollen to a bare patch where bees had no blossoms",
        magic_action="promised the crown a new purpose and sprinkled it with patient sunlight",
        invitation="Help us honor the garden, and we will share the flowers",
        helper_action="settled the crown around a young seedling instead of a head",
        reveal="the crown was guided by a garden spirit who wanted the ceremony to bless new life",
        ending="The seedling wore the crown, and tomorrow's flowers seemed to wave from underneath.",
        lesson="Honor can grow larger when it is shared with the future.",
    ),
    "mirror": CeremonyPlan(
        purpose="hold a mirror ceremony to thank the river for its shining path",
        trouble="the little mirror showed an empty sky instead of any faces",
        clue="noticed a silver fish swimming inside the reflection",
        first_try="wiped the glass, but the fish only winked and swam deeper",
        hidden_need="was searching for its lost school beyond the bend",
        magic_action="turned the mirror toward the river and spoke a rhyme of returning ripples",
        invitation="Follow the shining path, and we will help you find your friends",
        helper_action="sent a silver beam over the water until distant fins answered",
        reveal="the mirror held a tiny water-spirit who knew the river's secret roads",
        ending="The spirit slipped home, and the mirror reflected every smiling face beside the bright river.",
        lesson="A ceremony can become a bridge when people listen for a lonely voice.",
    ),
}

VERSE_STYLES = [
    ("On ceremony day, Luna made a plan; ", "with ribbons and bells for each woman and man."),
    ("The ceremony sparkled, the moon climbed high; ", "while silver-blue wishes went sailing by."),
    ("A rhyme was prepared, a bright banner was spun; ", "the ceremony waited for everyone."),
    ("Beneath a star, with a song in the air, ", "the ceremony gathered friends everywhere."),
    ("Luna swept the steps with a magical broom; ", "then set little candles to brighten the room."),
    ("The drums made a dum and the chimes made a ding; ", "the ceremony promised a marvelous thing."),
]

SURPRISE_STYLES = [
    "No one expected what happened next.",
    "Then came a surprise, as round as the moon.",
    "But magic was waiting behind the old tune.",
    "A secret was stirring, invisible and bright.",
    "The quietest corner began to take flight.",
    "The guests held their breath, and the stars held theirs too.",
]

ASP_RULES = r"""
ceremony_ready(S) :- setting(S), purpose(celebration), prepared(token).
surprise(S) :- ceremony_ready(S), hidden_need(guest), magic_used.
welcoming(S) :- surprise(S), invited(guest), helper(guest).
valid_story(S) :- ceremony_ready(S), welcoming(S), revealed(magic).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines.extend(
        [
            asp.fact("purpose", "celebration"),
            asp.fact("prepared", "token"),
            asp.fact("hidden_need", "guest"),
            asp.fact("magic_used", "magic"),
            asp.fact("invited", "guest"),
            asp.fact("helper", "guest"),
            asp.fact("revealed", "magic"),
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
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    expected = {("moonlit courtyard",), ("village green",), ("hilltop garden",), ("river meadow",)}
    actual = set(asp.atoms(model, "valid_story"))
    if actual == expected:
        print(f"OK: ASP and Python agree on {len(expected)} valid settings.")
        return 0
    print("MISMATCH between Python and ASP.")
    print("only python:", sorted(expected - actual))
    print("only asp:", sorted(actual - expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ceremony surprise magic rhyming storyworld.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--guest")
    parser.add_argument("--token")
    parser.add_argument("--ceremony", choices=CEREMONIES)
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
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(HERO_NAMES),
        guest=args.guest or rng.choice(GUEST_NAMES),
        token=args.token or rng.choice(TOKENS),
        ceremony=args.ceremony or rng.choice(list(CEREMONIES)),
        verse_style=rng.randrange(len(VERSE_STYLES)),
        surprise_style=rng.randrange(len(SURPRISE_STYLES)),
    )


def validate(params: StoryParams) -> None:
    if params.hero.strip().lower() == params.guest.strip().lower():
        raise StoryError("The hero and guest need different names so their dialogue is clear.")
    if not params.hero.strip() or not params.guest.strip():
        raise StoryError("The hero and guest must both have names.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown ceremony setting: {params.setting}.")
    if params.ceremony not in CEREMONIES:
        raise StoryError(f"Unknown ceremony plan: {params.ceremony}.")


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World(SETTINGS[params.setting])
    hero = world.add(
        Entity(
            "hero",
            ENTITY_HUMAN,
            "child",
            params.hero,
            meters={"prepared": 1.0, "calm": 0.0},
            memes={"wonder": 1.0, "worry": 0.0, "kindness": 0.0},
            location="ceremony steps",
        )
    )
    guest = world.add(
        Entity(
            "guest",
            ENTITY_MAGIC,
            "mysterious guest",
            params.guest,
            meters={"hidden": 1.0, "helpful": 0.0, "glow": 0.0},
            memes={"shyness": 1.0, "trust": 0.0, "joy": 0.0},
            location="quiet corner",
        )
    )
    token = world.add(
        Entity(
            "token",
            ENTITY_OBJECT,
            "ceremony token",
            params.token,
            meters={"ready": 1.0, "lost": 0.0, "bright": 0.0},
            owner="hero",
            location="ceremony table",
        )
    )
    world.facts.update(
        params=params,
        plan=CEREMONIES[params.ceremony],
        hero=hero,
        guest=guest,
        token=token,
        clue_seen=False,
        need_understood=False,
        invited=False,
        magic_used=False,
        revealed=False,
        resolved=False,
    )
    return world


def act_opening(world: World) -> None:
    params = world.facts["params"]
    plan = world.facts["plan"]
    hero = world.get("hero")
    token = world.get("token")
    first, second = VERSE_STYLES[params.verse_style]
    world.say(f"{first}{second}")
    world.say(f"In {world.setting}, {hero.label} prepared {token.label} to {plan.purpose}.")
    world.say(f"{hero.label} checked every ribbon and whispered, “Let this ceremony bring everyone near.”")


def act_trouble(world: World) -> None:
    plan = world.facts["plan"]
    hero = world.get("hero")
    token = world.get("token")
    token.meters["ready"] = 0.0
    token.meters["lost"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(f"But {plan.trouble}.")
    world.say(f"{hero.label} tried to fix it: {hero.label} {plan.first_try}.")
    world.say(f"{SURPRISE_STYLES[world.facts['params'].surprise_style]} “Did you see that?” asked {hero.label}. “I saw a glow, but not its way.”")


def act_clue(world: World) -> None:
    plan = world.facts["plan"]
    hero = world.get("hero")
    guest = world.get("guest")
    hero.memes["calm"] = 1.0
    guest.location = "beneath the old stone table"
    world.facts["clue_seen"] = True
    world.say(f"{hero.label} looked more closely and {plan.clue}.")
    world.say(f"The guest whispered, “Please do not chase me. I {plan.hidden_need}.”")
    world.say(f"{hero.label} answered, “Then tell me what you need, and we will make the ceremony kind.”")
    world.facts["need_understood"] = True


def act_magic(world: World) -> None:
    plan = world.facts["plan"]
    hero = world.get("hero")
    guest = world.get("guest")
    token = world.get("token")
    hero.memes["kindness"] = 1.0
    guest.memes["trust"] = 1.0
    token.meters["lost"] = 0.0
    token.meters["bright"] = 1.0
    world.facts["invited"] = True
    world.facts["magic_used"] = True
    world.say(f"{hero.label} lifted {token.label} and {plan.magic_action}.")
    world.say(f"“{plan.invitation},” said {hero.label}.")
    world.say(f“The guest peeked out. “May I really help?” “Yes,” said {hero.label}. “Your way may be the best way.”")


def act_resolution(world: World) -> None:
    plan = world.facts["plan"]
    guest = world.get("guest")
    guest.meters["hidden"] = 0.0
    guest.meters["helpful"] = 1.0
    guest.meters["glow"] = 1.0
    guest.memes["shyness"] = 0.0
    guest.memes["joy"] = 1.0
    guest.location = "ceremony circle"
    world.facts["revealed"] = True
    world.say(f"Then the surprise came: {plan.reveal}.")
    world.say(f"{guest.label} {plan.helper_action}. The ceremony began, and every guest joined the rhyme.")
    world.say(f"“The magic was not hiding the light,” said {hero.label}. “It was waiting for a welcome.”")
    world.say(plan.ending)
    world.say(plan.lesson)
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_opening(world)
    world.para()
    act_trouble(world)
    act_clue(world)
    act_magic(world)
    world.para()
    act_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    plan = world.facts["plan"]
    return [
        f"Write a child-friendly rhyming story about a ceremony in {world.setting}.",
        f"Show how {params.hero} discovers that {params.guest} {plan.hidden_need}.",
        f"Include Surprise and Magic, with a dialogue exchange that changes the ceremony.",
        f"End with this image: {plan.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    plan = world.facts["plan"]
    return [
        QAItem(
            question=f"What ceremony was {params.hero} preparing?",
            answer=f"{params.hero} was preparing a ceremony to {plan.purpose}.",
        ),
        QAItem(
            question=f"What went wrong before the ceremony began?",
            answer=f"{plan.trouble.capitalize()}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} understand the surprise?",
            answer=f"{params.hero} noticed that {plan.clue}.",
        ),
        QAItem(
            question=f"What did {params.guest} need?",
            answer=f"{params.guest} {plan.hidden_need}.",
        ),
        QAItem(
            question="How did the dialogue change what happened?",
            answer=f"{params.hero} invited the guest by saying, “{plan.invitation}” and then listened instead of chasing.",
        ),
        QAItem(
            question="What magical action helped solve the problem?",
            answer=f"{params.hero} {plan.magic_action}.",
        ),
        QAItem(
            question="What proved that the ceremony had a happy ending?",
            answer=f"{plan.ending}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ceremony?",
            answer="A ceremony is a special gathering or set of actions used to mark an important moment.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that changes what people think will happen.",
        ),
        QAItem(
            question="What is magic in this story world?",
            answer="Magic is a gentle story force that helps people notice hidden needs and make hopeful changes.",
        ),
        QAItem(
            question="Why can a welcome matter?",
            answer="A welcome can help a frightened or lonely guest feel safe enough to share what they need.",
        ),
        QAItem(
            question="What makes a rhyming story?",
            answer="A rhyming story uses repeated sound patterns and musical language while still telling a clear sequence of events.",
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
            f"{entity.id}: {entity.label} ({entity.type}), "
            f"location={entity.location}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"facts: {world.facts['clue_seen']=}, {world.facts['need_understood']=}, "
                 f"{world.facts['invited']=}, {world.facts['magic_used']=}, "
                 f"{world.facts['revealed']=}, {world.facts['resolved']=}")
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        setting="moonlit courtyard",
        hero="Luna",
        guest="Bram",
        token="silver bell",
        ceremony="lantern",
        verse_style=0,
        surprise_style=0,
    ),
    StoryParams(
        setting="village green",
        hero="Mira",
        guest="Clover",
        token="blue ribbon",
        ceremony="ribbon",
        verse_style=1,
        surprise_style=1,
    ),
    StoryParams(
        setting="hilltop garden",
        hero="Nell",
        guest="Moss",
        token="golden leaf",
        ceremony="crown",
        verse_style=2,
        surprise_style=2,
    ),
    StoryParams(
        setting="river meadow",
        hero="Willa",
        guest="Dew",
        token="glowing pebble",
        ceremony="mirror",
        verse_style=3,
        surprise_style=3,
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
        for (setting,) in asp_valid():
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
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

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
            header = f"### {params.hero} / {params.guest} / {params.ceremony} in {params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
