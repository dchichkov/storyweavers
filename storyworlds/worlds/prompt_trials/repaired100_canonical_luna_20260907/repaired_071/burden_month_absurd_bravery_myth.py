#!/usr/bin/env python3
"""
Standalone storyworld: a child-friendly myth about a burden, a month, and
the absurd shape courage can take.

The village of Bellroot carries one impossible burden: every month, the moon
drops a stone bell into the town square. Bravery does not erase the burden.
Instead, a child discovers that naming its absurdity lets the whole village
share it, changing fear into a useful ritual.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str
    village: str
    month: str
    burden: str
    seed: Optional[int] = None


HEROES = ["Luna", "Mira", "Tavi", "Niko", "Sela", "Orin"]
VILLAGES = ["Bellroot", "Mossmere", "Cloudstep", "Thistleford"]
MONTHS = ["January", "April", "July", "October"]
BURDENS = [
    "the moon's stone bell",
    "a sack of sleeping thunder",
    "the emperor's enormous spoon",
    "a shadow that demanded breakfast",
]

MONTH_DATA = {
    "January": {"weather": "frosty", "image": "silver frost on the roofs"},
    "April": {"weather": "rainy", "image": "rain beads shining on the road"},
    "July": {"weather": "bright", "image": "heat trembling above the stones"},
    "October": {"weather": "windy", "image": "red leaves racing past the well"},
}


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(self.events)


@dataclass(frozen=True)
class Myth:
    burden_problem: str
    first_attempt: str
    strange_clue: str
    brave_action: str
    cause: str
    shared_ritual: str
    ending_image: str
    lesson: str


MYTHS = [
    Myth(
        burden_problem="the stone bell was so heavy that it bent the square's oldest flagpole",
        first_attempt="the mayor ordered twelve oxen to pull it uphill, but the oxen sat down and began chewing the rope",
        strange_clue="each time someone complained about the bell, it became one pebble lighter",
        brave_action="stood beside the bell and announced that it was the silliest burden in the whole sky",
        cause="the moon had made the bell from all the complaints people hid inside themselves",
        shared_ritual="each person carried one small pebble to the fountain and told the truth about one worry",
        ending_image="the moon lifted the empty bell rope while a ring of tiny pebbles glittered around the fountain",
        lesson="Bravery can begin by saying plainly what feels impossible",
    ),
    Myth(
        burden_problem="the thunder sack blocked the bakery door and rumbled whenever anyone tried to squeeze past",
        first_attempt="the strongest adults pushed it with a cart, but the cart rolled backward and delivered everyone to the chicken coop",
        strange_clue="the sack grew quieter whenever someone laughed at its ridiculous size",
        brave_action="climbed onto the doorstep and thanked the sack for being absurdly dramatic",
        cause="the storm king had packed every unspoken fear into one sack so the village could see it",
        shared_ritual="the villagers wrote their fears on leaves, folded them into boats, and floated them down the stream",
        ending_image="the empty sack became a picnic blanket beneath a sky washed clean",
        lesson="A strange burden may shrink when courage gives it a name",
    ),
    Myth(
        burden_problem="the enormous spoon lay across the bridge and stirred the river whenever the wind blew",
        first_attempt="the villagers tried to use it for soup, but the river tasted of clouds and one fisherman caught a button",
        strange_clue="the spoon tilted toward anyone who admitted feeling afraid",
        brave_action="walked to its handle and confessed, loudly, that the spoon frightened her",
        cause="a giant had dropped the spoon after trying to stir the village's hidden worries",
        shared_ritual="the villagers took turns holding the handle while naming one fear and one hope",
        ending_image="the spoon rested beside the bridge as a shining signpost pointing toward home",
        lesson="Courage is not pretending to be fearless; it is making room for truth",
    ),
    Myth(
        burden_problem="the hungry shadow followed the village bell-ringer and demanded breakfast from every doorway",
        first_attempt="the cooks offered porridge, pies, and three turnips, but the shadow swallowed the plates and stayed hungry",
        strange_clue="the shadow grew shorter whenever somebody asked what it truly needed",
        brave_action="faced the shadow at noon and asked its question before offering it another meal",
        cause="the shadow had been made from everyone's fear of being forgotten",
        shared_ritual="the villagers gathered at dusk and told stories about one another so no one stood alone",
        ending_image="the shadow curled beneath the story tree, small enough to sleep beside a child's shoe",
        lesson="Bravery listens to a burden before trying to push it away",
    ),
]


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        [params.hero, params.village, params.month, params.burden]
    )
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def build_world(params: StoryParams) -> World:
    if params.month not in MONTH_DATA:
        raise StoryError(f"Unknown month: {params.month}")
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero: {params.hero}")
    if params.village not in VILLAGES:
        raise StoryError(f"Unknown village: {params.village}")
    if params.burden not in BURDENS:
        raise StoryError(f"Unknown burden: {params.burden}")

    rng = random.Random(stable_seed(params) ^ 0xB7A5)
    myth = rng.choice(MYTHS)
    weather = MONTH_DATA[params.month]

    world = World(params)
    hero = world.add(
        Entity(
            "hero",
            "person",
            params.hero,
            meters={"courage": 0.0, "distance": 0.0},
            memes={"fear": 1.0, "bravery": 0.0, "belonging": 0.0},
        )
    )
    village = world.add(
        Entity(
            "village",
            "place",
            params.village,
            meters={"burden": 8.0, "month_day": 1.0},
            memes={"worry": 1.0, "hope": 0.0},
        )
    )
    burden = world.add(
        Entity(
            "burden",
            "object",
            params.burden,
            meters={"weight": 8.0, "absurdity": 9.0},
            memes={"complaints": 0.0, "quiet": 0.0},
        )
    )

    world.facts.update(hero=hero, village=village, burden=burden, myth=myth)

    world.say(
        f"In the {weather['weather']} month of {params.month}, when "
        f"{weather['image']}, the village of {params.village} received its "
        f"monthly burden from the sky."
    )
    world.say(
        f"It was {params.burden}, an absurd object so large that even the "
        f"village dogs barked at it from a respectful distance."
    )
    world.say(
        f"{params.hero}, who was small enough to borrow the baker's stool, "
        f"watched the burden settle in the square."
    )
    world.say(
        f"The village bell-ringer cried, \"Not again! This burden is too much "
        f"for one village.\""
    )
    world.say(
        f"{params.hero} answered, \"Then let us not pretend it is ordinary. "
        f"What does it do when we tell the truth about it?\""
    )

    world.say("")
    world.say(myth.burden_problem.capitalize() + ".")
    world.say(
        f"Everyone tried to solve the problem at once. {myth.first_attempt.capitalize()}."
    )
    burden.memes["complaints"] += 1.0
    village.memes["worry"] += 1.0
    world.say(
        f"At last, {params.hero} noticed something no grown-up had written in "
        f"the village book: {myth.strange_clue}."
    )
    world.say(
        f"The bell-ringer whispered, \"Should we send for a hero?\" "
        f"{params.hero} said, \"A hero can be the person who takes the first "
        f"honest step.\""
    )

    world.say("")
    world.say(
        f"That was when {params.hero} chose bravery. {params.hero} "
        f"{myth.brave_action}."
    )
    hero.meters["courage"] += 1.0
    hero.memes["fear"] = 0.0
    hero.memes["bravery"] += 1.0
    burden.memes["quiet"] += 1.0
    world.say(
        f"The burden gave a deep, ridiculous sigh. Then the truth became clear: "
        f"{myth.cause}."
    )
    world.say(
        f"The bell-ringer asked, \"Does bravery mean carrying everything alone?\""
    )
    world.say(
        f"\"No,\" said {params.hero}. \"It means beginning honestly, so others "
        f"know how to help.\""
    )

    world.say("")
    world.say(
        f"So the people of {params.village} made a new custom for every "
        f"{params.month}: {myth.shared_ritual}."
    )
    village.meters["burden"] = 2.0
    village.memes["worry"] = 0.0
    village.memes["hope"] = 1.0
    hero.memes["belonging"] += 1.0
    burden.meters["weight"] = 2.0
    world.say(
        f"With each shared truth, {params.burden} grew lighter. It did not "
        f"vanish, because even myths know that burdens deserve care."
    )
    world.say(
        f"By moonrise, {myth.ending_image.capitalize()}."
    )
    world.say(
        f"{params.hero} wrote the village lesson on the bell-ringer's new book: "
        f"\"{myth.lesson}.\""
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.facts["hero"]
    myth = world.facts["myth"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a myth about {params.hero}, a monthly burden, and bravery.",
            f"Tell a child-friendly story in which {params.burden} seems absurd but teaches a useful truth.",
            f"Write a myth set in {params.village} during {params.month}, where a shared ritual changes a burden.",
        ],
        story_qa=[
            QAItem(
                question=f"What burden arrived in {params.village} during {params.month}?",
                answer=(
                    f"During {params.month}, {params.village} received "
                    f"{params.burden} as its monthly burden from the sky."
                ),
            ),
            QAItem(
                question=f"How did {params.hero} show bravery?",
                answer=(
                    f"{params.hero} showed bravery by {myth.brave_action}. "
                    f"This honest action helped the village understand the burden."
                ),
            ),
            QAItem(
                question="Why did the burden become lighter?",
                answer=(
                    f"The burden became lighter because {myth.cause}. "
                    f"The villagers shared their worries instead of hiding them."
                ),
            ),
            QAItem(
                question="What did the villagers do together?",
                answer=(
                    f"They made a monthly ritual: {myth.shared_ritual}. "
                    f"Sharing the ritual changed fear into cooperation."
                ),
            ),
            QAItem(
                question="What lesson did the myth teach?",
                answer=f"The myth taught that {myth.lesson}.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a burden?",
                answer="A burden is something difficult or heavy that a person or group must carry or manage.",
            ),
            QAItem(
                question="What does absurd mean?",
                answer="Absurd means so strange or unreasonable that it can seem silly.",
            ),
            QAItem(
                question="What is bravery?",
                answer="Bravery is taking a helpful or honest action even when you feel afraid.",
            ),
            QAItem(
                question="What is a month?",
                answer="A month is a named part of the year made of several weeks.",
            ),
        ],
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    village = args.village or rng.choice(VILLAGES)
    month = args.month or rng.choice(MONTHS)
    burden = args.burden or rng.choice(BURDENS)
    return StoryParams(
        hero=hero,
        village=village,
        month=month,
        burden=burden,
        seed=args.seed,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a myth about a monthly absurd burden and bravery."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--village", choices=VILLAGES)
    parser.add_argument("--month", choices=MONTHS)
    parser.add_argument("--burden", choices=BURDENS)
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: kind={entity.kind} meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid_month(M) :- month(M).
valid_burden(B) :- burden(B).
valid_story(M,B) :- valid_month(M), valid_burden(B).
shared_burden(M,B) :- valid_story(M,B).
"""


def asp_facts() -> str:
    import asp

    facts = []
    facts.extend(asp.fact("month", month.lower()) for month in MONTHS)
    facts.extend(
        asp.fact("burden", burden.replace(" ", "_"))
        for burden in BURDENS
    )
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> set[tuple[str, str]]:
    return {(month.lower(), burden.replace(" ", "_")) for month in MONTHS for burden in BURDENS}


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = valid_combos()
    if actual != expected:
        print("MISMATCH between ASP and Python registries.")
        print("Only in ASP:", sorted(actual - expected))
        print("Only in Python:", sorted(expected - actual))
        return 1

    for index, (month, burden) in enumerate(sorted(expected)[:4]):
        params = StoryParams(
            hero=HEROES[index % len(HEROES)],
            village=VILLAGES[index % len(VILLAGES)],
            month=next(m for m in MONTHS if m.lower() == month),
            burden=next(b for b in BURDENS if b.replace(" ", "_") == burden),
            seed=9000 + index,
        )
        sample = generate(params)
        if not sample.story or params.hero not in sample.story:
            print("Generated-story exercise failed.")
            return 1

    print(f"OK: ASP/Python parity verified for {len(expected)} month-burden pairs.")
    return 0


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
        print()
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
        print("Compatible month-burden combinations:")
        for month, burden in sorted(valid_combos()):
            print(f"  {month} + {burden}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, month in enumerate(MONTHS):
            params = StoryParams(
                hero=HEROES[index % len(HEROES)],
                village=VILLAGES[index % len(VILLAGES)],
                month=month,
                burden=BURDENS[index % len(BURDENS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
