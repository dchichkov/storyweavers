#!/usr/bin/env python3
"""
A tiny pirate tale storyworld about a historic shutter, friendship, and
problem solving on a dockside ship.

Seed premise:
- A little harbor has an old, historic shutter in the captain's cabin.
- The shutter keeps sticking, which makes the cabin dark and causes trouble.
- Two pirate friends must solve the problem together.
- Their friendship helps them listen, share tools, and fix the shutter.

The story is stateful:
- physical meters track light, grip, rust, and repair
- emotional memes track worry, trust, patience, and cheer
- dialogue changes what the pirates know and do
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the dockside harbor"
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    trouble: str
    wrong_plan: str
    clue: str
    shared_action: str
    repair_step: str
    result: str
    ending_image: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter(e, key) + amt


def add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme(e, key) + amt


SETTING = Setting(
    place="the dockside harbor",
    affords={"listen", "fix", "share", "test"},
)

SCENARIOS = [
    Scenario(
        "rusted_hinge",
        "The captain's cabin held a historic shutter that had watched a hundred storms from the same small window.",
        "When the wind rose, the shutter stuck halfway shut and left the cabin gloomy as a cave.",
        "One pirate wanted to yank it hard with both hands and be done with it.",
        "A thin line of rust glittered on the lower hinge where salt spray had dried.",
        "share the lantern oil and the clean rag",
        "carefully brush the rust, then lift the shutter together",
        "the shutter swung open and the cabin filled with bright sea light",
        "sunlight striped the maps on the wall and the old shutter stayed open",
        "friendship and patience can solve a stubborn problem better than rough hands",
    ),
    Scenario(
        "loose_latch",
        "A historic shutter on the captain's cabin clicked like a tiny drum when the ship rolled.",
        "Each click woke the sleeping parrot and frightened the chart boy below.",
        "The first idea was to nail the shutter shut forever.",
        "The latch had a bent tongue that slipped free whenever the deck tilted.",
        "use a pocket knife and a short strip of leather",
        "bend the tongue back and tie a soft leather catch",
        "the shutter stayed still even when the ship swayed",
        "the parrot slept and the chart boy smiled at last",
        "a shared fix can be kinder than a harsh one",
    ),
    Scenario(
        "salt_swell",
        "The harbor mist soaked the cabin window until the old shutter swelled like wet bread.",
        "Now it scraped the frame and made a shrill noise every time anyone tried to close it.",
        "One pirate guessed the answer was to splash it with more water.",
        "A dry plank beside the stove showed the wood would shrink if warmed slowly.",
        "carry the plank and the kettle of warm steam",
        "warm the frame little by little and guide the shutter by hand",
        "the wood eased back and the scrape faded away",
        "the cabin grew quiet except for gulls outside",
        "careful problem solving beats a rushed guess",
    ),
    Scenario(
        "rope_pull",
        "The historic shutter was tied to a rope so the captain could shut out the moon when she slept.",
        "But the rope had tangled in a knot that would not budge.",
        "One pirate wanted to cut the rope and forget the knot.",
        "A loose loop near the cleat showed the rope had only crossed itself, not broken.",
        "share the cutlass handle as a lever and the little marlinspike",
        "untie the crossed loops before pulling once more",
        "the rope slid free and the shutter moved smooth as a gull's wing",
        "the captain could darken the cabin without losing the rope",
        "looking closely keeps a useful tool from becoming waste",
    ),
    Scenario(
        "paint_peel",
        "The shutter's blue paint was old enough to be called historic by every sailor in port.",
        "But the peeling flakes jammed the rails and left the cabin half dark.",
        "One pirate wanted to scrape all the paint away in a rush.",
        "Under the flakes, the wood was fine and only the loose edges needed trimming.",
        "share the scraper and the little brush",
        "trim the peeling edges and polish the rails before testing again",
        "the shutter slid cleanly and kept its proud blue color",
        "the cabin looked neat and the shutter kept its story",
        "good repairs protect the past while fixing the present",
    ),
    Scenario(
        "bird_nest",
        "A sparrow had built a nest in the gap behind the historic shutter.",
        "Whenever the shutter moved, the nest shook and the chicks chirped in alarm.",
        "One pirate nearly slammed the window shut to scare the bird away.",
        "A feather stuck in the gap showed the nest had to be moved gently, not ruined.",
        "share a shoelace and a soft cap for carrying the nest",
        "lift the nest to a safer beam and guide the shutter slowly",
        "the sparrow settled on the beam and the shutter worked again",
        "the cabin stayed bright without troubling the chicks",
        "friendship includes taking care with small lives",
    ),
]

DIALOGUES = [
    "What is the shutter trying to tell us?",
    "Could we fix it if we look at the small part first?",
    "What can we share so both of us can help?",
    "Should we force it, or should we listen to it?",
    "What if the problem is only pretending to be bigger?",
    "May I hold the lantern while you test the hinge?",
]

REFLECTIONS = [
    "A good pirate does not just grab treasure; a good pirate also grabs the right idea.",
    "Friends make better repairs when they trust each other enough to slow down.",
    "A stubborn thing often yields to patience before strength.",
    "Looking closely can turn a mystery into a simple job.",
    "The best crew is the one that fixes trouble without making new trouble.",
]

PIRATE_NAMES = [
    "Nell",
    "Mara",
    "Rook",
    "Finn",
    "Tessa",
    "Jory",
]

PIRATE_NICKNAMES = [
    "the Bright Hook",
    "the Quick Gull",
    "the Salt Fox",
    "the Little Cap'n",
    "the Lantern Mate",
]

ADJ = ["brave", "cheerful", "clever", "patient", "bold", "kind"]


@dataclass
class StoryParams:
    place: str
    scenario: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate tale about a historic shutter, friendship, and problem solving."
    )
    ap.add_argument("--place", choices=["harbor"])
    ap.add_argument("--scenario", choices=[s.id for s in SCENARIOS])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scenario = args.scenario or rng.choice([s.id for s in SCENARIOS])
    name = args.name or rng.choice(PIRATE_NAMES)
    friend = args.friend or rng.choice([n for n in PIRATE_NAMES if n != name])
    trait = args.trait or rng.choice(ADJ)
    return StoryParams("harbor", scenario, name, friend, trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "harbor":
        raise StoryError("This pirate tale only sails in a harbor.")
    if params.scenario not in {s.id for s in SCENARIOS}:
        raise StoryError("Unknown shutter scenario.")


def prop(world: World, params: StoryParams) -> World:
    variant = params.seed if params.seed is not None else sum((i + 1) * ord(ch) for i, ch in enumerate(
        f"{params.name}|{params.friend}|{params.trait}|{params.scenario}"
    ))
    scenario = next(s for s in SCENARIOS if s.id == params.scenario)
    dialogue = DIALOGUES[variant % len(DIALOGUES)]
    reflection = REFLECTIONS[(variant // len(DIALOGUES)) % len(REFLECTIONS)]

    hero = world.add(Entity(id=params.name, kind="character", type="pirate", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="pirate", label=params.friend))
    shutter = world.add(Entity(id="shutter", kind="thing", type="shutter", label="historic shutter"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="lantern"))

    add_meme(hero, "worry", 1.0)
    add_meme(friend, "trust", 1.0)
    world.say(
        f"In the dockside harbor, {hero.id} and {friend.id} served on a small pirate crew with plenty of ropes, maps, and salt air."
    )
    world.say(
        f"They both knew the captain's cabin had a historic shutter, older than the ship's newest sails and fussier than a cat in rain."
    )
    world.say(scenario.opening)
    world.para()

    world.say(scenario.trouble)
    world.say(f"{hero.id} said, 'This is a real pirate problem.'")
    world.say(f"{friend.id} answered, 'Then let us solve it like a crew.'")
    world.say(scenario.wrong_plan)
    add_meme(hero, "impulse", 1.0)

    world.para()
    world.say(f"{hero.id} held up the lantern and asked, '{dialogue}'")
    world.say(f"{friend.id} leaned close and said, 'Look at the small part first.'")
    world.say(scenario.clue)
    add_meme(hero, "curiosity", 1.0)
    add_meme(hero, "patience", 1.0)
    add_meter(hero, "light", 1.0)
    add_meter(friend, "light", 1.0)

    world.para()
    world.say(
        f"Together they chose to {scenario.shared_action}."
    )
    world.say(
        f"{hero.id} cleaned while {friend.id} steadied the frame, and their friendship kept them from tugging too hard."
    )
    add_meter(hero, "repair", 1.0)
    add_meter(friend, "repair", 1.0)
    add_meme(friend, "cheer", 1.0)

    world.say(f"Then they {scenario.repair_step}.")
    add_meter(shutter, "open", 1.0)
    add_meter(shutter, "repair", 1.0)
    add_meter(lantern, "light", 1.0)
    add_meme(hero, "pride", 1.0)
    add_meme(friend, "trust", 1.0)

    world.para()
    world.say(f"The result was easy to see: {scenario.result}.")
    world.say(
        f"The captain laughed from the doorway and said, 'That is the sort of work I like to see.'"
    )
    world.say(
        f"{hero.id} grinned at {friend.id} and replied, 'A friend makes a better tool than a hammer.'"
    )
    world.say(f"{reflection} {scenario.lesson}.")
    world.say(scenario.ending_image)

    world.facts.update(
        hero=hero,
        friend=friend,
        shutter=shutter,
        lantern=lantern,
        scenario=scenario,
        dialogue=dialogue,
        reflection=reflection,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    world = prop(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scenario = f["scenario"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        f"Write a short pirate tale about a historic shutter that causes trouble in a harbor cabin.",
        f"Tell a child-friendly story where {hero.id} and {friend.id} solve a problem by working together.",
        f"Include a brief dialogue that helps fix this problem: {scenario.trouble}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    scenario = f["scenario"]
    return [
        QAItem(
            question="Who had the problem to solve?",
            answer=f"{hero.id} and {friend.id} had to solve the problem together in the harbor cabin.",
        ),
        QAItem(
            question="What was wrong with the shutter?",
            answer=f"The historic shutter was stuck and caused trouble because {scenario.trouble.lower()}",
        ),
        QAItem(
            question="What clue helped the pirates fix it?",
            answer=f"The clue was this detail: {scenario.clue}",
        ),
        QAItem(
            question="What did the pirates share?",
            answer=f"They shared help and tools by {scenario.shared_action}.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They solved it by {scenario.repair_step}.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"At the end, {scenario.result}, and the cabin looked different because the shutter worked again.",
        ),
        QAItem(
            question="What did friendship do in the story?",
            answer="Friendship kept the pirates calm, helped them talk, and made the repair work smoothly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a panel that opens or closes over a window to let light in or keep it out.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means finding a good way to fix something that is wrong or difficult.",
        ),
        QAItem(
            question="Why is friendship helpful?",
            answer="Friendship is helpful because friends can share work, listen carefully, and encourage each other.",
        ),
        QAItem(
            question="Why do pirates use lanterns at night?",
            answer="Pirates use lanterns so they can see inside cabins, along decks, and in the dark harbor.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(harbor, historic_shutter_friendship_problem_solving_pirate_tale).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "harbor"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
            asp.fact("style", "pirate_tale"),
            asp.fact("seed_word", "historic"),
            asp.fact("seed_word", "shutter"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    return [("harbor", "historic_shutter_friendship_problem_solving_pirate_tale")]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combo).")
        return 0
    print("MISMATCH")
    return 1


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
    StoryParams("harbor", "rusted_hinge", "Nell", "Mara", "kind"),
    StoryParams("harbor", "loose_latch", "Rook", "Finn", "patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.scenario}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
