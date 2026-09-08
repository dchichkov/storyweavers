#!/usr/bin/env python3
"""
A standalone storyworld about Zig, Acid, and Cod solving a dangerous sharing problem.

The domain uses sharing, dialogue, and problem solving in a child-facing superhero
story. The world model tracks physical meters and emotional memes, and the prose
is produced by state changes rather than by a frozen paragraph.
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
ENTITY_ANIMAL = "animal"
ENTITY_OBJECT = "object"


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

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == ENTITY_HUMAN:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == ENTITY_ANIMAL:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

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

    def record(self, event: str) -> None:
        self.events.append(event)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.events = list(self.events)
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    acid: str
    cod: str
    challenge: str = "power_cell"
    opening_style: int = 0
    danger_style: int = 0
    dialogue_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Challenge:
    object_name: str
    premise: str
    danger: str
    clue: str
    first_plan: str
    need: str
    shared_plan: str
    helper_action: str
    resolution: str
    ending: str
    lesson: str


SETTINGS = {
    "Skyline Harbor": "the bright towers of Skyline Harbor",
    "Moonbridge City": "the busy streets of Moonbridge City",
    "Cloudrail Station": "the high platforms of Cloudrail Station",
    "Sunwheel Square": "the spinning fountain at Sunwheel Square",
}

HERO_NAMES = ["Luna", "Mira", "Nova", "Tess", "Ari", "Juno"]
ACID_NAMES = ["Acid", "Aci", "Drip", "Fizz"]
COD_NAMES = ["Cod", "Cody", "Fin", "Silver"]

CHALLENGES = {
    "power_cell": Challenge(
        object_name="the moon battery",
        premise="had found a moon battery that could light every dark street",
        danger="the battery slipped from a rooftop cart and began rolling toward a storm drain",
        clue="noticed Acid's sharp green glow could mark the battery's path without touching it",
        first_plan="tried to grab the battery alone, but the spinning wheels made her cape snag on a railing",
        need="was able to see the safest path through the battery's flickering shadows",
        shared_plan="asked Acid to light the safe turns while Cod blocked the drain with his broad fins",
        helper_action="sent a careful beam around each corner and warned everyone when the pavement tilted",
        resolution="Luna guided the moon battery into a padded rescue box instead of the drain",
        ending="When the lights came on, the three heroes' shadows joined on the wall like one enormous guardian.",
        lesson="Sharing a job can make a hard rescue safer and stronger.",
    ),
    "rainbow_bridge": Challenge(
        object_name="the rainbow bridge crystal",
        premise="had discovered a rainbow bridge crystal that connected two separated neighborhoods",
        danger="the crystal cracked, and a gust began carrying its bright pieces over the river",
        clue="saw that Acid could soften the sharp edges while Cod could carry pieces through the shallow water",
        first_plan="rushed after the largest piece, but nearly slipped on the wet bridge stones",
        need="could smell which crystal pieces were safe to gather first",
        shared_plan="gave Acid the job of sealing cracks and Cod the job of ferrying the pieces",
        helper_action="sealed each tiny crack with a glowing touch while Cod carried the safe pieces",
        resolution="Luna fitted the pieces together only after Acid and Cod had prepared them",
        ending="The restored bridge made a rainbow under their boots, with one color for every helping hand.",
        lesson="Listening to each hero's special skill turns scattered trouble into a shared solution.",
    ),
    "cloud_seed": Challenge(
        object_name="the sky-garden seed",
        premise="had promised to plant a sky-garden seed above the city",
        danger="the seed pod opened too soon and sent silver roots crawling across the flying tram",
        clue="learned that Acid could dissolve the metal vines gently while Cod could hold the tram steady",
        first_plan="pulled at a vine, but the tram lurched and made the passengers wobble",
        need="was strong enough to keep the tram steady but needed help knowing which vines to release",
        shared_plan="let Acid loosen one vine at a time while Cod braced the tram and Luna guided the roots",
        helper_action="melted only the vines Luna pointed to, leaving the living seed root unharmed",
        resolution="Luna moved the seed pod into a quiet rooftop planter",
        ending="By sunset, the first cloud-leaf opened above the tram line like a green superhero cape.",
        lesson="Problem solving means protecting the important part while changing the dangerous part.",
    ),
    "star_map": Challenge(
        object_name="the lost star map",
        premise="had found a star map that could guide lost travelers home",
        danger="the map's ink spilled across three streets and began erasing its own directions",
        clue="realized Acid could separate the wet ink while Cod could remember the map's reflected lines",
        first_plan="pressed the map flat, but the ink spread into a giant blue puddle",
        need="could see the hidden lines beneath the spill but needed a steady light",
        shared_plan="asked Acid to clear small windows in the ink while Cod read each revealed turn aloud",
        helper_action="opened one clean patch at a time and waited for Cod's spoken directions",
        resolution="Luna redrew the route on a dry cloth before the last star disappeared",
        ending="The rescued map glowed above the station, pointing home for every traveler who looked up.",
        lesson="Dialogue helps different kinds of knowledge fit together.",
    ),
}

OPENINGS = [
    "{hero} was a young superhero who believed the brightest power was a power shared.",
    "Above {setting}, {hero} practiced superhero rescues with careful feet and an open heart.",
    "The city knew {hero} as a quick hero, but {hero} knew that quick did not always mean alone.",
    "Whenever trouble flashed across the skyline, {hero} looked first for a way to help everyone help.",
    "{hero} wore a silver cape, a bright badge, and a promise never to keep a useful idea secret.",
    "The superhero alarm rang just as {hero} was teaching a small team that every skill mattered.",
]

DANGER_LINES = [
    "The warning bell gave three nervous clangs.",
    "A red beacon spun across the clouds.",
    "The pavement trembled under a rush of frightened footsteps.",
    "A gust whipped around the rooftops and tugged at every loose thing.",
    "The city lights blinked as if they were asking for help.",
]

DIALOGUE_STYLES = [
    (
        '"I can lift it!" {hero} said.',
        '"I can guide it," {acid} replied.',
        '"And I can guard the way," {cod} added.',
    ),
    (
        '"What can your power do safely?" {hero} asked.',
        '"I can show the edges," {acid} said.',
        '"I can hold the center," {cod} answered.',
    ),
    (
        '"Let us name the danger before we rush," {hero} said.',
        '"The sharp turn is the danger," {acid} told her.',
        '"Then I will watch that turn," {cod} promised.',
    ),
    (
        '"No hero should have to solve this alone," {hero} said.',
        '"Good," said {acid}. "My glow is ready."',
        '"And my fins are ready too," said {cod}.',
    ),
]

ASP_RULES = r"""
% The shared plan is valid only when each teammate contributes a distinct skill.
safe_rescue(S) :-
    setting(S),
    has_danger(S),
    dialogue_done,
    acid_guides,
    cod_guards,
    hero_shares_plan.

% A complete superhero story has a safe rescue rather than a reckless grab.
complete_story(S) :-
    safe_rescue(S),
    object_saved,
    team_together.
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("setting", key) for key in SETTINGS]
    lines.extend(
        [
            asp.fact("has_danger", key)
            for key in SETTINGS
        ]
    )
    lines.extend(
        [
            asp.fact("dialogue_done"),
            asp.fact("acid_guides"),
            asp.fact("cod_guards"),
            asp.fact("hero_shares_plan"),
            asp.fact("object_saved"),
            asp.fact("team_together"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show complete_story/1."))
    return sorted(set(asp.atoms(model, "complete_story")))


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show safe_rescue/1."))
    actual = set(s for (s,) in asp.atoms(model, "safe_rescue"))
    expected = set(SETTINGS)
    if actual != expected:
        print("MISMATCH between Python and ASP story coverage.")
        print("only python:", sorted(expected - actual))
        print("only asp:", sorted(actual - expected))
        return 1

    for setting in SETTINGS:
        if not asp.atoms(model, "safe_rescue"):
            print("ASP produced no safe rescue.")
            return 1

    rng = random.Random(20260907)
    for _ in range(8):
        params = resolve_params(
            argparse.Namespace(
                setting=None,
                hero=None,
                acid=None,
                cod=None,
            ),
            rng,
        )
        sample = generate(params)
        if not sample.story or "said" not in sample.story:
            print("Generated story verification failed.")
            return 1

    print(f"OK: ASP and Python agree on {len(expected)} settings; generated stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Zig, Acid, and Cod superhero sharing storyworld."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--acid")
    parser.add_argument("--cod")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HERO_NAMES)
    acid = args.acid or rng.choice(ACID_NAMES)
    cod = args.cod or rng.choice(COD_NAMES)
    return StoryParams(
        setting=setting,
        hero=hero,
        acid=acid,
        cod=cod,
        challenge=rng.choice(list(CHALLENGES)),
        opening_style=rng.randrange(len(OPENINGS)),
        danger_style=rng.randrange(len(DANGER_LINES)),
        dialogue_style=rng.randrange(len(DIALOGUE_STYLES)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.hero.strip() or not params.acid.strip() or not params.cod.strip():
        raise StoryError("The hero, Acid, and Cod each need a non-empty name.")
    names = {params.hero.casefold(), params.acid.casefold(), params.cod.casefold()}
    if len(names) != 3:
        raise StoryError("The hero, Acid, and Cod need different names.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}.")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"Unknown challenge: {params.challenge}.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(SETTINGS[params.setting])

    hero = world.add(
        Entity(
            id="hero",
            kind=ENTITY_HUMAN,
            type="superhero",
            label=params.hero,
            phrase=f"the young superhero {params.hero}",
            meters={"courage": 1.0, "focus": 1.0},
            memes={"kindness": 1.0, "worry": 0.0, "confidence": 1.0},
            location="rooftop",
        )
    )
    acid = world.add(
        Entity(
            id="acid",
            kind=ENTITY_HUMAN,
            type="glow-helper",
            label=params.acid,
            phrase=f"the glowing helper {params.acid}",
            meters={"glow": 1.0, "control": 0.0},
            memes={"worry": 1.0, "belonging": 0.0, "confidence": 0.5},
            location="rooftop",
        )
    )
    cod = world.add(
        Entity(
            id="cod",
            kind=ENTITY_ANIMAL,
            type="heroic-cod",
            label=params.cod,
            phrase=f"the sturdy superhero cod named {params.cod}",
            meters={"strength": 1.0, "balance": 1.0, "guarding": 0.0},
            memes={"worry": 1.0, "pride": 0.0, "belonging": 0.0},
            location="rooftop pool",
        )
    )
    rescue_object = world.add(
        Entity(
            id="rescue_object",
            kind=ENTITY_OBJECT,
            type="rescue-object",
            label=CHALLENGES[params.challenge].object_name,
            phrase=CHALLENGES[params.challenge].object_name,
            meters={"safe": 0.0, "moving": 1.0, "saved": 0.0},
            location="dangerous edge",
        )
    )

    world.facts.update(
        params=params,
        challenge=CHALLENGES[params.challenge],
        hero=hero,
        acid=acid,
        cod=cod,
        rescue_object=rescue_object,
        danger_seen=False,
        dialogue_done=False,
        plan_shared=False,
        object_saved=False,
        team_together=False,
        resolved=False,
    )
    return world


def predict_rescue(world: World) -> dict[str, bool]:
    simulation = world.copy()
    obj = simulation.get("rescue_object")
    acid = simulation.get("acid")
    cod = simulation.get("cod")
    hero = simulation.get("hero")
    safe = (
        hero.memes.get("kindness", 0.0) > 0
        and acid.meters.get("control", 0.0) > 0
        and cod.meters.get("guarding", 0.0) > 0
        and obj.meters.get("saved", 0.0) > 0
    )
    return {"safe": safe}


def act_opening(world: World) -> None:
    params = world.facts["params"]
    hero = world.get("hero")
    challenge = world.facts["challenge"]
    world.say(
        OPENINGS[params.opening_style].format(
            hero=hero.label,
            setting=world.setting,
        )
    )
    world.say(
        f"That day, {hero.label} {challenge.premise} in {world.setting}."
    )
    world.record("The hero discovered the rescue object and chose to protect it.")


def act_danger(world: World) -> None:
    hero = world.get("hero")
    obj = world.get("rescue_object")
    acid = world.get("acid")
    cod = world.get("cod")
    challenge = world.facts["challenge"]

    obj.location = "near the dangerous edge"
    hero.memes["worry"] = 1.0
    acid.memes["worry"] = 1.0
    cod.memes["worry"] = 1.0
    world.facts["danger_seen"] = True

    world.say(DANGER_LINES[world.facts["params"].danger_style])
    world.say(
        f"Suddenly, {challenge.danger}. {obj.phrase.capitalize()} wobbled close to danger."
    )
    world.say(f"{hero.label} {challenge.first_plan}.")
    world.record("A lone first attempt failed because the moving object was too risky to grab.")
    world.say(
        f"{hero.label} stopped and looked at {acid.label} and {cod.label}. "
        "A superhero plan needed more than one pair of hands."
    )


def act_dialogue(world: World) -> None:
    hero = world.get("hero")
    acid = world.get("acid")
    cod = world.get("cod")
    challenge = world.facts["challenge"]
    style = DIALOGUE_STYLES[world.facts["params"].dialogue_style]

    world.say(style[0].format(hero=hero.label))
    world.say(style[1].format(acid=acid.label))
    world.say(style[2].format(cod=cod.label))
    world.say(f"Then {hero.label} discovered the clue: {challenge.clue}.")
    world.say(
        f"{acid.label} explained that {challenge.need}. "
        f"{cod.label} nodded and said, 'Tell me where to stand.'"
    )

    acid.memes["belonging"] = 1.0
    cod.memes["belonging"] = 1.0
    world.facts["dialogue_done"] = True
    world.record("Dialogue revealed what Acid and Cod could safely contribute.")


def act_share_plan(world: World) -> None:
    hero = world.get("hero")
    acid = world.get("acid")
    cod = world.get("cod")
    challenge = world.facts["challenge"]

    world.say(
        f"{hero.label} shared the plan: {challenge.shared_plan.capitalize()}."
    )
    world.say(
        f'"I will call out each step," {hero.label} said. '
        f'"{acid.label}, show us the safe path. {cod.label}, guard the danger."'
    )
    acid.meters["control"] = 1.0
    cod.meters["guarding"] = 1.0
    hero.memes["confidence"] = 2.0
    world.facts["plan_shared"] = True
    world.record("The hero shared the plan instead of keeping control alone.")


def act_teamwork(world: World) -> None:
    hero = world.get("hero")
    acid = world.get("acid")
    cod = world.get("cod")
    challenge = world.facts["challenge"]

    world.say(f"{acid.label} {challenge.helper_action}.")
    world.say(
        f"{cod.label} held the dangerous edge steady while {hero.label} "
        "moved only when the next safe signal appeared."
    )
    world.say(
        f"The three teammates checked one another after every step: "
        f"{acid.label} watched the light, {cod.label} watched the edge, and "
        f"{hero.label} watched the whole rescue."
    )
    world.facts["team_together"] = True
    world.record("The team used distinct skills and checked the plan through dialogue.")


def act_resolution(world: World) -> None:
    hero = world.get("hero")
    acid = world.get("acid")
    cod = world.get("cod")
    obj = world.get("rescue_object")
    challenge = world.facts["challenge"]

    challenge_resolution = challenge.resolution
    world.say(f"{hero.label} {challenge_resolution}.")
    world.say(
        f"{acid.label} dimmed the glow, {cod.label} relaxed his fins, and "
        f"{hero.label} shared a grateful high-five with both teammates."
    )
    world.say(challenge.ending)
    world.say(challenge.lesson)

    obj.location = "safe rescue box"
    obj.meters["moving"] = 0.0
    obj.meters["safe"] = 1.0
    obj.meters["saved"] = 1.0
    acid.memes["worry"] = 0.0
    acid.memes["confidence"] = 1.0
    cod.memes["worry"] = 0.0
    cod.memes["pride"] = 1.0
    hero.memes["worry"] = 0.0
    world.facts["object_saved"] = True
    world.facts["resolved"] = True
    world.record("The rescue object reached safety because the shared plan was followed.")


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_opening(world)
    world.para()
    act_danger(world)
    act_dialogue(world)
    act_share_plan(world)
    act_teamwork(world)
    world.para()
    act_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    challenge = world.facts["challenge"]
    return [
        f"Write a child-friendly superhero story about {params.hero}, Acid, and Cod in {world.setting}.",
        f"Show how the team solves this danger: {challenge.danger}.",
        f"Include sharing and dialogue, then end with this image: {challenge.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    hero = world.get("hero")
    acid = world.get("acid")
    cod = world.get("cod")
    challenge = world.facts["challenge"]

    return [
        QAItem(
            question=f"What did {hero.label} discover in {world.setting}?",
            answer=f"{hero.label} discovered {challenge.object_name}, which {challenge.premise.split(' had ', 1)[-1]}.",
        ),
        QAItem(
            question=f"What danger threatened {challenge.object_name}?",
            answer=f"{challenge.object_name.capitalize()} was in danger because {challenge.danger}.",
        ),
        QAItem(
            question=f"Why did {hero.label}'s first plan fail?",
            answer=f"{hero.label}'s first plan failed because {challenge.first_plan}.",
        ),
        QAItem(
            question=f"What did dialogue reveal about {acid.label} and {cod.label}?",
            answer=f"The dialogue revealed that {acid.label} {challenge.need}, while {cod.label} could contribute strength and guarding.",
        ),
        QAItem(
            question="How did the heroes share the work?",
            answer=f"{hero.label} shared the plan: {challenge.shared_plan.capitalize()}",
        ),
        QAItem(
            question=f"How was {challenge.object_name} saved?",
            answer=f"{challenge.resolution.capitalize()} The team checked each step together, so the rescue stayed safe.",
        ),
        QAItem(
            question="What changed in the team by the end?",
            answer=f"Acid and Cod were no longer worried teammates standing apart; they became confident partners who trusted the shared plan.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving others a fair chance to use an idea, resource, or responsibility instead of keeping everything for yourself.",
        ),
        QAItem(
            question="Why is dialogue useful during a problem?",
            answer="Dialogue lets people explain what they know, ask questions, and choose a safer plan together.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing the danger, understanding its cause, trying a careful plan, and changing the plan when needed.",
        ),
        QAItem(
            question="What makes someone a superhero in this story world?",
            answer="A superhero protects others, listens before rushing, and shares useful powers so the whole team can succeed.",
        ),
        QAItem(
            question="Who are Acid and Cod?",
            answer="Acid is a glowing helper who can carefully mark or change a dangerous path, and Cod is a sturdy superhero fish who can guard and steady things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
    lines = ["--- world trace ---", f"setting: {world.setting}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.label} ({entity.type}); "
            f"location={entity.location}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append("events:")
    lines.extend(f"- {event}" for event in world.events)
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
        setting="Skyline Harbor",
        hero="Luna",
        acid="Acid",
        cod="Cod",
        challenge="power_cell",
        opening_style=0,
        danger_style=0,
        dialogue_style=0,
    ),
    StoryParams(
        setting="Moonbridge City",
        hero="Mira",
        acid="Fizz",
        cod="Fin",
        challenge="rainbow_bridge",
        opening_style=1,
        danger_style=1,
        dialogue_style=1,
    ),
    StoryParams(
        setting="Cloudrail Station",
        hero="Nova",
        acid="Drip",
        cod="Cody",
        challenge="cloud_seed",
        opening_style=2,
        danger_style=2,
        dialogue_style=2,
    ),
    StoryParams(
        setting="Sunwheel Square",
        hero="Tess",
        acid="Aci",
        cod="Silver",
        challenge="star_map",
        opening_style=3,
        danger_style=3,
        dialogue_style=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show complete_story/1."))
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
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 30):
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            try:
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

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
                f"### {params.hero} / {params.acid} / {params.cod} "
                f"in {params.setting}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
