#!/usr/bin/env python3
"""
A small superhero storyworld about a hero, a grizzly problem, a cleaning quest,
and a happy ending.

Seed image:
---
A young superhero hears that a grizzly is causing trouble in a city garden.
Instead of fighting, the hero listens to an inner monologue, takes on a quest
to scour away the mess, and learns that the real problem is a broken honey
drum causing confusion. The hero uses a kind spoken exchange to change the plan,
finishes the quest, and ends with a happy ending.
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
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample  # eager import


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Nova"
    sidekick_name: str = "Milo"
    city_name: str = "Maple City"
    garden_name: str = "Sunrise Garden"


HERO_NAMES = ["Nova", "Ruby", "Ace", "Sky", "Jade", "Iris", "Bolt", "Piper"]
SIDEKICK_NAMES = ["Milo", "Tess", "Leo", "Maya", "Nia", "Finn", "Lena", "Owen"]
CITY_NAMES = ["Maple City", "Bright Harbor", "Clover Point", "Rivergate", "Skyline Park"]
GARDEN_NAMES = ["Sunrise Garden", "Lantern Garden", "Pollen Park", "Moonbeam Garden", "Westside Green"]


INCIDENTS = [
    {
        "title": "the muddy statue path",
        "problem": "a giant grizzly footprint trail",
        "misunderstanding": "the grizzly was breaking lamps",
        "truth": "a broken honey drum was spilling sweet syrup and drawing the bear in circles",
        "quest": "scour the path clean and guide the grizzly away from the syrup",
        "action": "used a sponge-brush, rang a warning bell, and swept the syrup into a bucket",
        "turn": "the grizzly stopped snuffling at the mess and followed the bell toward the pond",
        "ending": "the statues shone again under the evening lights while the garden smelled like rain and flowers",
        "lesson": "A hero's best power is often careful thinking before a loud move",
    },
    {
        "title": "the toppled picnic lane",
        "problem": "a row of crushed picnic baskets",
        "misunderstanding": "the grizzly wanted to steal lunch",
        "truth": "a squirrel had cracked the honey drum, and the grizzly only wanted the sticky smell to stop",
        "quest": "scour the lane for clues and repair the broken drum",
        "action": "followed paw prints, picked up wrappers, and tied the drum back with a bright blue cord",
        "turn": "when the drum quieted, the grizzly yawned and sat peacefully beside the hedge",
        "ending": "the families returned, and the picnic lane filled with sandwiches, laughter, and a careful bear-sized path",
        "lesson": "Even a messy day can become a good one when someone looks closer",
    },
    {
        "title": "the windy fountain square",
        "problem": "trash spinning around the fountain",
        "misunderstanding": "the grizzly was making a storm on purpose",
        "truth": "the wind had shaken loose a honey drum lid, and the bear was only chasing the smell",
        "quest": "scour the square, find the lid, and calm the grizzly",
        "action": "lifted a metal grate, scooped leaves from the water, and showed the bear a safer trail",
        "turn": "the grizzly sniffed the fixed drum, then lumbered after the safer trail with a calm huff",
        "ending": "the fountain sparkled, the trash was gone, and children clapped from the steps",
        "lesson": "A clear clue can turn fear into a plan",
    },
    {
        "title": "the rooftop garden",
        "problem": "a trail of smashed flowerpots",
        "misunderstanding": "the grizzly was angry at the city",
        "truth": "a bee had hidden in the honey drum, and the grizzly chased the buzzing by mistake",
        "quest": "scour the roof, rescue the flowers, and end the chase",
        "action": "carried each pot to safety, opened the drum, and let the bee fly free",
        "turn": "the grizzly settled down when the buzzing stopped and sniffed the rooftop herbs instead",
        "ending": "new flowers stood in a neat row, and the rooftop glowed with sunset colors",
        "lesson": "Kindness can calm what force only worsens",
    },
    {
        "title": "the subway mural hall",
        "problem": "paint smudged across a bright wall",
        "misunderstanding": "the grizzly had ruined the mural",
        "truth": "the honey drum was leaking, and the bear had slipped on the sweet mess",
        "quest": "scour the wall, help the grizzly, and save the mural",
        "action": "wiped the paint, spread salt on the sticky floor, and patched the drum with tape",
        "turn": "the grizzly sniffed the cleaned floor, then ambled politely toward the exit",
        "ending": "the mural showed a smiling city again, and the hallway looked brave and new",
        "lesson": "A hero should fix the cause, not just the visible damage",
    },
    {
        "title": "the moonlit bridge",
        "problem": "a jam of broken crates",
        "misunderstanding": "the grizzly was blocking the bridge",
        "truth": "the bear had gotten stuck trying to lick honey from a drum wedged under the rail",
        "quest": "scour the bridge, free the grizzly, and clear the way home",
        "action": "moved the crates, slid the drum out, and guided the grizzly with a soft whistle",
        "turn": "the grizzly crossed gently once the sticky trap was gone",
        "ending": "cars rolled across the bridge again while the river kept shining below",
        "lesson": "Sometimes rescue looks more like untangling than triumph",
    },
    {
        "title": "the schoolyard path",
        "problem": "mud tracked into the playground",
        "misunderstanding": "the grizzly had chased the children",
        "truth": "the honey drum had rolled from the supply shed, and the grizzly followed its sweet scent",
        "quest": "scour the mud, calm the crowd, and roll the drum back",
        "action": "rinsed the swings, spoke kindly to the teachers, and pushed the drum into the shed",
        "turn": "the grizzly sat outside the fence while the children waved from the slides",
        "ending": "the playground shone clean, and recess began with happy cheers",
        "lesson": "When everyone stays calm, a scary moment can shrink fast",
    },
    {
        "title": "the harbor flower beds",
        "problem": "saltwater splashed into the soil",
        "misunderstanding": "the grizzly wanted the boats",
        "truth": "the bear had been licking leaked honey from the drum near the docks",
        "quest": "scour the beds, protect the flowers, and lead the grizzly inland",
        "action": "poured fresh water on the soil, planted new seeds, and pointed out a berry bush",
        "turn": "the grizzly chose the berry bush instead of the drum and stopped pacing",
        "ending": "the harbor smelled sweet again, and the flowers bowed in the breeze",
        "lesson": "A better choice can appear once the real need is known",
    },
    {
        "title": "the library courtyard",
        "problem": "pages scattered through the grass",
        "misunderstanding": "the grizzly had torn the books",
        "truth": "the honey drum had burst under a bench, and the bear had chased the smell into the courtyard",
        "quest": "scour the grass, gather the pages, and keep the bear safe",
        "action": "sorted the pages, mended the drum lid, and read aloud in a steady voice",
        "turn": "the grizzly grew calm at the sound and sat like a statue beside the bench",
        "ending": "the librarians smiled, and the courtyard became quiet and golden at dusk",
        "lesson": "A gentle voice can be stronger than a fearful guess",
    },
    {
        "title": "the train station steps",
        "problem": "a slippery trail of syrup",
        "misunderstanding": "the grizzly was waiting to attack",
        "truth": "the honey drum had burst from a cart, and the bear was only curious and hungry",
        "quest": "scour the steps, guide the bear, and fix the cart",
        "action": "scrubbed the syrup, fastened the cart wheel, and offered the grizzly an apple from a safe distance",
        "turn": "the grizzly took the apple, then waddled off without a single growl",
        "ending": "the station clock rang on time, and the steps sparkled like glass",
        "lesson": "What looks like a threat can sometimes be a confused creature needing care",
    },
]


TELLING_MODES = [
    ("The city woke up to trouble in the garden.", "The hero answered by listening first and acting second."),
    ("At first, the grizzly problem seemed huge and loud.", "A careful clue changed the whole mission."),
    ("The night patrol expected a chase.", "Instead, the hero started a thoughtful quest."),
    ("The garden looked messy, but not every mess was the same kind.", "That difference saved the day."),
    ("A superhero cape can make a big shadow, but it cannot solve every mystery alone.", "The inner monologue helped the hero choose better."),
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.hero_name, kind="character", type="hero", label=params.hero_name))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="hero", label=params.sidekick_name))
    city = world.add(Entity(id="city", kind="place", type="city", label=params.city_name))
    garden = world.add(Entity(id="garden", kind="place", type="garden", label=params.garden_name))
    grizzly = world.add(Entity(id="grizzly", kind="character", type="animal", label="grizzly"))
    drum = world.add(Entity(id="drum", kind="thing", type="thing", label="honey drum"))
    broom = world.add(Entity(id="broom", kind="thing", type="tool", label="broom"))

    hero.meters["energy"] = 1.0
    hero.memes["worry"] = 0.2
    sidekick.meters["helpfulness"] = 1.0
    garden.meters["mess"] = 1.0
    grizzly.meters["distance"] = 5.0
    grizzly.memes["confusion"] = 1.0
    drum.meters["leak"] = 1.0
    broom.meters["bristles"] = 1.0

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        city=city,
        garden=garden,
        grizzly=grizzly,
        drum=drum,
        broom=broom,
    )


def _selection_token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.hero_name}|{params.sidekick_name}|{params.city_name}|{params.garden_name}"
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    city = world.facts["city"]
    garden = world.facts["garden"]
    grizzly = world.facts["grizzly"]
    drum = world.facts["drum"]

    token = _selection_token(params)
    incident = INCIDENTS[token % len(INCIDENTS)]
    mode = TELLING_MODES[(token // len(INCIDENTS)) % len(TELLING_MODES)]

    world.say(mode[0])
    world.say(
        f"In {params.city_name}, {hero.label} and {sidekick.label} flew over {params.garden_name} in their bright capes. "
        f"Below them, {incident['problem']} made the flower paths look wrong."
    )
    world.say(
        f"The first report said {incident['misunderstanding']}. {hero.label} felt a rush of worry, "
        f"and the grizzly's loud footsteps shook the garden fence."
    )
    world.say(
        f"Inside {hero.label}'s head, a sharp inner monologue said, "
        f"\"Don't rush. Look. Listen. This is a quest, not just a chase.\""
    )

    world.para()
    world.say(
        f"{sidekick.label} pointed to the shiny mess near the bench. \"Do you think the grizzly did it?\" "
        f"{hero.label} answered, \"Maybe not. Let's scour the area and find the real clue.\""
    )
    world.say(
        f"Together they began the quest to {incident['quest']}. "
        f"They used the broom, checked the grass, and followed the sticky trail to the broken drum."
    )
    world.say(
        f"The truth was kinder than the first guess: {incident['truth']}."
    )

    world.para()
    world.say(
        f"{hero.label} said, \"Grizzly, easy now. We know what happened.\" "
        f"The grizzly gave a small huff, which sounded less like anger and more like tired confusion."
    )
    world.say(
        f"{sidekick.label} asked, \"What should we do first?\" "
        f"{hero.label} replied, \"Fix the drum, scour the path, and make the garden safe.\""
    )
    world.say(
        f"So they {incident['action']}. As the sticky trail disappeared, the grizzly stopped circling and listened."
    )
    world.say(
        f"That change mattered. The bear was not chasing trouble anymore; it was only waiting for the sweet smell to fade."
    )

    world.para()
    world.say(
        f"At last, {incident['turn']}. "
        f"{hero.label} felt the panic leave their chest like a cloud opening."
    )
    world.say(
        f"{hero.label} and {sidekick.label} led the grizzly toward a berry patch beyond the hedge. "
        f"The animal lumbered after them peacefully, and the garden grew quiet again."
    )
    world.say(
        f"{incident['ending']}. {incident['lesson']}."
    )
    world.say(
        f'{hero.label} smiled and said, "Quest complete." '
        f'{sidekick.label} grinned back. "And a happy ending too."'
    )

    hero.meters["energy"] = 0.6
    hero.memes["worry"] = 0.0
    sidekick.meters["helpfulness"] = 1.0
    garden.meters["mess"] = 0.0
    grizzly.meters["distance"] = 15.0
    grizzly.memes["confusion"] = 0.1
    drum.meters["leak"] = 0.0

    world.facts.update(
        params=params,
        incident=incident,
        incident_index=token % len(INCIDENTS),
        mode_index=(token // len(INCIDENTS)) % len(TELLING_MODES),
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story(params: StoryParams) -> bool:
    if not params.hero_name or not params.sidekick_name:
        return False
    if params.hero_name == params.sidekick_name:
        return False
    if params.city_name == params.garden_name:
        return False
    return True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a superhero story about {p.hero_name} and {p.sidekick_name} in {p.city_name}, where a grizzly causes trouble at {p.garden_name}.",
        f"Include an inner monologue, a quest to scour away a mess, a spoken exchange, and a happy ending.",
        f"Show how a mistaken grizzly problem becomes a kinder solution once the hero finds the real cause of the mess: {incident['truth']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    grizzly = world.facts["grizzly"]

    return [
        QAItem(
            question=f"Where did {hero.label} and {sidekick.label} go on their quest?",
            answer=f"They went to {p.garden_name} in {p.city_name} to deal with the grizzly trouble there.",
        ),
        QAItem(
            question="What did the hero's inner monologue tell them to do?",
            answer="It told the hero not to rush, but to look and listen carefully before acting.",
        ),
        QAItem(
            question="What did the crew first think was happening?",
            answer=f"They thought {incident['misunderstanding']}. That guess made the problem seem more dangerous than it really was.",
        ),
        QAItem(
            question="What was the real cause of the trouble?",
            answer=f"{incident['truth'].capitalize()}.",
        ),
        QAItem(
            question="What was the quest the hero had to complete?",
            answer=f"They had to {incident['quest']}.",
        ),
        QAItem(
            question="What changed after the hero and sidekick spoke to the grizzly?",
            answer=f"After they said, \"Grizzly, easy now,\" the bear calmed down and followed the safer path. Their words helped the bear understand they were there to help.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily: {incident['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large bear with a strong body, shaggy fur, and a reputation for being powerful.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to clean something thoroughly or search an area very carefully.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem is solved and the story finishes in a good and peaceful way.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
heroic_story(S) :- inner_monologue(S), quest(S), grizzly_problem(S).
problem_understood(S) :- heroic_story(S), found_truth(S).
happy_ending(S) :- problem_understood(S), kind_exchange(S), quest_complete(S).
valid_story(S) :- happy_ending(S).
"""


def asp_facts() -> str:
    from storyworlds import asp

    lines = [
        asp.fact("inner_monologue", "story1"),
        asp.fact("quest", "story1"),
        asp.fact("grizzly_problem", "story1"),
        asp.fact("found_truth", "story1"),
        asp.fact("kind_exchange", "story1"),
        asp.fact("quest_complete", "story1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("story1",)} if valid_story(StoryParams()) else set()
    if atoms == py:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about a grizzly problem, a cleaning quest, and a happy ending.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--city-name", choices=CITY_NAMES)
    ap.add_argument("--garden-name", choices=GARDEN_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    city = args.city_name or rng.choice(CITY_NAMES)
    garden = args.garden_name or rng.choice(GARDEN_NAMES)
    return StoryParams(seed=None, hero_name=hero, sidekick_name=sidekick, city_name=city, garden_name=garden)


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid story parameters: hero/sidekick must differ and city/garden must differ.")
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(hero_name="Nova", sidekick_name="Milo", city_name="Maple City", garden_name="Sunrise Garden"),
    StoryParams(hero_name="Ruby", sidekick_name="Tess", city_name="Bright Harbor", garden_name="Lantern Garden"),
    StoryParams(hero_name="Ace", sidekick_name="Finn", city_name="Clover Point", garden_name="Moonbeam Garden"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
