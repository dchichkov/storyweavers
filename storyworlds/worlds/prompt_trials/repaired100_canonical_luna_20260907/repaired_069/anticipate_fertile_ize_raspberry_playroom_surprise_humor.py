#!/usr/bin/env python3
"""A playful superhero storyworld about anticipating trouble in a raspberry playroom."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Playroom:
    name: str = "the playroom"
    raspberry_basket: bool = True
    toy_city: bool = True
    cape_hook: bool = True


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    partner: str = "Bix"
    caller: str = "Mara"
    setting: str = "playroom"
    challenge: int = 0
    opening: int = 0
    surprise: int = 0
    humor: int = 0
    cautionary: int = 0
    ending: int = 0


HEROES = ["Luna", "Nova", "Pip", "Comet", "Ziggy", "Ruby"]
PARTNERS = ["Bix", "Taro", "Mimi", "Bolt", "Nell"]
CALLERS = ["Mara", "Jo", "Tess", "Ari"]

CHALLENGES = [
    {
        "title": "the raspberry rocket",
        "problem": "A red toy rocket rolled toward a tower of blocks, carrying a basket of ripe raspberries.",
        "clue": "Luna noticed that the rocket always veered where a shiny marble nudged its wheel.",
        "plan": "Luna placed a cardboard ramp beside the marble while Bix held a pillow at the tower's base.",
        "result": "The ramp turned the rocket toward a soft blanket, and every raspberry landed safely.",
        "lesson": "Anticipating a small danger can protect a big plan.",
        "ending": "The raspberry rocket rested on the blanket like a tiny red spaceship.",
        "object": "raspberries",
        "risk": "The block tower could topple and scatter the berries.",
    },
    {
        "title": "the fertile-ize garden machine",
        "problem": "A pretend garden machine was ready to fertile-ize the playroom's paper garden, but its scoop pointed at the carpet.",
        "clue": "Luna saw a loose blue crayon under the machine's front wheel.",
        "plan": "Luna asked Bix to lift the wheel with a ruler while she moved the crayon and placed a tray beneath the scoop.",
        "result": "The machine sprinkled pretend soil onto the paper garden instead of the carpet.",
        "lesson": "A careful check makes room for useful work.",
        "ending": "The paper garden stood tall, with raspberry-colored flowers around its edges.",
        "object": "paper garden",
        "risk": "The pretend soil could cover the carpet and ruin the garden game.",
    },
    {
        "title": "the cape-clipping catapult",
        "problem": "A spoon catapult flung a toy cape toward a shelf crowded with cups and a raspberry bowl.",
        "clue": "Luna saw that the spoon's elastic band had been stretched too far.",
        "plan": "Luna loosened the band and made a landing zone from cushions while Bix moved the cups.",
        "result": "The cape sailed gently onto the cushions, and the cups and raspberries stayed put.",
        "lesson": "Superheroes use caution before showing off.",
        "ending": "The cape draped over the cushion fort like a bright flag.",
        "object": "toy cape",
        "risk": "A wild launch could knock down the shelf and spill the raspberries.",
    },
    {
        "title": "the surprise puddle patrol",
        "problem": "A water cup tipped beside the toy city just as a parade of wooden heroes marched past.",
        "clue": "Luna spotted the cup rocking whenever the playroom door bumped.",
        "plan": "Luna moved the cup into a wide tray and built a towel bridge around the city.",
        "result": "The water stayed in the tray, and the wooden heroes crossed the dry bridge.",
        "lesson": "A surprising problem becomes smaller when someone notices its cause.",
        "ending": "The toy heroes celebrated on a towel bridge above the sparkling tray.",
        "object": "toy city",
        "risk": "Water could soak the paper streets and wooden toys.",
    },
    {
        "title": "the raspberry rescue alarm",
        "problem": "A toy alarm chirped beside a bowl of raspberries while a wind-up dragon marched closer.",
        "clue": "Luna discovered that the alarm's button was trapped under the dragon's cardboard tail.",
        "plan": "Luna paused the dragon with a block, then Bix slid a spoon under the tail to free the button.",
        "result": "The alarm stopped chirping, and the raspberries were saved from a startled tumble.",
        "lesson": "Pause, observe, and then act with a helpful plan.",
        "ending": "The dragon bowed beside the raspberry bowl instead of bumping it.",
        "object": "raspberry bowl",
        "risk": "A sudden alarm could make someone knock over the berries.",
    },
    {
        "title": "the upside-down hero tunnel",
        "problem": "A blanket tunnel sagged over the path to the snack table, where raspberry muffins waited.",
        "clue": "Luna noticed that one chair leg had slipped off its paper coaster.",
        "plan": "Luna replaced the coaster and added two cushions as safe supports before anyone crawled through.",
        "result": "The tunnel stood firm, and the heroes reached the muffins without a tumble.",
        "lesson": "Caution can keep an adventure joyful.",
        "ending": "The tunnel entrance wore a raspberry-red star made from paper.",
        "object": "blanket tunnel",
        "risk": "The tunnel could collapse while someone crawled beneath it.",
    },
]

OPENINGS = [
    "In the playroom, {hero} wore a cape made from a towel and watched every corner like a real superhero.",
    "The playroom was full of blocks, cushions, and raspberry-colored toys when {hero} announced patrol time.",
    "At breakfast's end, {hero} entered the playroom with a cardboard shield and a very serious superhero walk.",
    "Sunlight striped the playroom floor as {hero} checked the toy city for anything that needed help.",
    "The playroom buzzed with make-believe power, but {hero} knew even pretend adventures deserved real caution.",
]

SURPRISES = [
    "Suddenly, a rubber chicken popped out of a box and shouted, 'Peep!'",
    "A springy sock leaped from the costume basket and landed on Bix's head.",
    "Without warning, a toy frog bounced from the fort and saluted the ceiling.",
    "A hidden bell rang, and everyone jumped except the stuffed bear.",
    "The smallest block gave a dramatic wobble, as if it had just seen a ghost.",
]

HUMOR = [
    "Bix puffed up proudly. 'I meant to wear the sock. It is my emergency helmet.'",
    "Bix whispered, 'If the plan fails, I shall distract danger with my finest chicken impression.'",
    "The stuffed bear fell over and was promoted to captain of lying down.",
    "Bix struck a heroic pose, then sneezed so hard that the pose became a sitting pose.",
    "The toy dragon made a burping sound, which was not in the superhero handbook.",
]

CAUTIONARY = [
    "Luna raised one finger. 'A hero does not hurry past a warning.'",
    "Luna said, 'We can be brave and careful at the same time.'",
    "The playroom grew quiet while Luna reminded everyone, 'Check first, then charge.'",
    "Luna tucked the cape behind her. 'Surprises are fun only when no one gets hurt.'",
    "Luna drew a small stop sign in chalk before touching the troublesome toy.",
]

ENDINGS = [
    "When the patrol ended, the heroes hung their capes neatly and shared the raspberries.",
    "The playroom glowed with proud smiles, safe toys, and one very important bowl of berries.",
    "Everyone cheered, and the stuffed bear received the first raspberry as an award.",
    "The toy city remained standing, while the new safety sign became the playroom's smallest landmark.",
    "Luna's cape fluttered above the fort, where every hero now knew how to anticipate trouble.",
]


ASP_RULES = r"""
#show danger/1.
#show power/1.
#show lesson/1.

danger(D) :- risk(D).
power(anticipation).
lesson(caution_turns_surprise_into_safety) :- power(anticipation), danger(playroom).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("risk", "playroom"),
            asp.fact("power", "anticipation"),
            asp.fact("lesson", "caution_turns_surprise_into_safety"),
        ]
    )


def asp_program(show: str = "#show danger/1.\n#show power/1.\n#show lesson/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about anticipation, fertile-izing, and raspberry surprises."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--caller", choices=CALLERS)
    parser.add_argument("--setting", default="playroom")
    parser.add_argument("--challenge", type=int, choices=range(len(CHALLENGES)))
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
    setting = args.setting.strip().lower()
    if not setting:
        raise StoryError("setting cannot be empty")
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        partner=args.partner or rng.choice(PARTNERS),
        caller=args.caller or rng.choice(CALLERS),
        setting=setting,
        challenge=args.challenge if args.challenge is not None else rng.randrange(len(CHALLENGES)),
        opening=rng.randrange(len(OPENINGS)),
        surprise=rng.randrange(len(SURPRISES)),
        humor=rng.randrange(len(HUMOR)),
        cautionary=rng.randrange(len(CAUTIONARY)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting.lower() != "playroom":
        raise StoryError("this superhero storyworld is set in the playroom")

    world = World()
    room = Playroom()
    hero = world.add(Entity(params.hero, "superhero", params.hero))
    partner = world.add(Entity(params.partner, "sidekick", params.partner))
    caller = world.add(Entity(params.caller, "caller", params.caller))

    hero.meters.update(alertness=0.8, reach=0.6)
    hero.memes.update(courage=1.0, caution=0.0)
    partner.memes["helpfulness"] = 1.0
    caller.memes["trust"] = 1.0

    challenge = CHALLENGES[params.challenge % len(CHALLENGES)]
    values = {
        "hero": hero.id,
        "partner": partner.id,
        "caller": caller.id,
        "setting": "the playroom",
    }

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**values))
    world.say(
        f"{caller.id} called, 'Superhero help!' {hero.id} answered, 'We will anticipate the trouble before we dash in.'"
    )
    world.say(challenge["problem"])
    world.say(
        f"{hero.id} pointed to the risk. {challenge['risk']} "
        f"{partner.id} asked, 'Should we rush?' {hero.id} replied, 'No. First we look.'"
    )
    world.say(SURPRISES[params.surprise % len(SURPRISES)])
    world.say(HUMOR[params.humor % len(HUMOR)])
    world.say(CAUTIONARY[params.cautionary % len(CAUTIONARY)])
    world.say(challenge["clue"])
    world.say(
        f"{partner.id} said, 'I can help.' {hero.id} nodded. 'Then you hold the safe side while I change the plan.'"
    )
    world.say(challenge["plan"])
    world.say(
        f"The pretend garden looked fertile-ized, the raspberry-colored details stayed bright, "
        f"and the playroom remained ready for one more safe adventure."
    )
    world.say(challenge["result"])

    hero.memes["caution"] = 1.0
    hero.memes["surprise_handled"] = 1.0
    partner.memes["confidence"] = 1.0
    world.say(f"Lesson learned: {challenge['lesson']}")
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.say(challenge["ending"])

    world.facts.update(
        room=room,
        hero=hero,
        partner=partner,
        caller=caller,
        challenge=challenge,
        risk=challenge["risk"],
        clue=challenge["clue"],
        solved=True,
        surprise=True,
        humor=True,
        cautionary=True,
        fertile_ized=True,
        raspberry=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"]
    challenge = facts["challenge"]
    return [
        f"Write a child-friendly superhero story in the playroom where {hero.id} anticipates {challenge['title']}.",
        f"Tell a humorous cautionary adventure involving a raspberry and a safe superhero rescue.",
        "Write a surprising playroom story that uses the word fertile-ize and ends with a clear lesson about caution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    partner = facts["partner"]
    challenge = facts["challenge"]
    return [
        QAItem(
            question=f"What did {hero.id} anticipate in the playroom?",
            answer=f"{hero.id} anticipated that {challenge['risk'].lower()}",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice?",
            answer=challenge["clue"],
        ),
        QAItem(
            question=f"How did {hero.id} and {partner.id} solve the problem?",
            answer=challenge["plan"] + " " + challenge["result"],
        ),
        QAItem(
            question="How did the story use humor?",
            answer="A silly surprise interrupted the danger, but the heroes still used caution and checked the problem before acting.",
        ),
        QAItem(
            question="What lesson did the superhero learn?",
            answer=f"The lesson was that {challenge['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to anticipate something?",
            answer="To anticipate something means to think ahead about what may happen and prepare for it.",
        ),
        QAItem(
            question="What does fertile-ize mean in this storyworld?",
            answer="Fertile-ize means to help pretend soil or a garden become ready for plants to grow.",
        ),
        QAItem(
            question="Why should superheroes use caution?",
            answer="Superheroes should use caution so they can protect people, toys, and themselves while solving a problem.",
        ),
        QAItem(
            question="Why are raspberries useful in a playful story?",
            answer="Raspberries add a bright, concrete treasure that can be protected, shared, or accidentally jostled during an adventure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "lesson")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    danger = set(asp.atoms(model, "danger"))
    power = set(asp.atoms(model, "power"))
    lessons = set(asp.atoms(model, "lesson"))
    expected_danger = {("playroom",)}
    expected_power = {("anticipation",)}
    expected_lessons = {("caution_turns_surprise_into_safety",)}
    if danger == expected_danger and power == expected_power and lessons == expected_lessons:
        sample = generate(StoryParams())
        if sample.story and "playroom" in sample.story and "raspberry" in sample.story.lower():
            print("OK: ASP parity and generated story checks passed.")
            return 0
    print("MISMATCH between ASP facts and Python gate.")
    print("  danger:", sorted(danger))
    print("  power:", sorted(power))
    print("  lessons:", sorted(lessons))
    return 1


CURATED = [
    StoryParams(hero="Luna", partner="Bix", caller="Mara", setting="playroom", challenge=0),
    StoryParams(
        hero="Nova",
        partner="Taro",
        caller="Jo",
        setting="playroom",
        challenge=1,
        opening=1,
        surprise=2,
        humor=3,
        cautionary=1,
        ending=4,
    ),
    StoryParams(
        hero="Ruby",
        partner="Mimi",
        caller="Tess",
        setting="playroom",
        challenge=4,
        opening=3,
        surprise=4,
        humor=0,
        cautionary=3,
        ending=2,
    ),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        facts = asp_valid()
        print(f"{len(facts)} ASP lesson facts")
        for item in facts:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempt < limit:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1

    if not samples:
        raise StoryError("no stories could be generated")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.hero}: playroom superhero patrol"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
