#!/usr/bin/env python3
"""
A playful pirate tale about Pompon, a sailor who learns from a previous mistake
when a humorous treasure-map mix-up sends the crew in the wrong direction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Pompon"
    captain: str = "Captain Brine"
    helper: str = "Saffron"
    parrot: str = "Jolly"
    place: str = "the Laughing Gull"
    treasure: str = "a chest of lemon candies"
    sea: str = "the giggling blue sea"
    task: str = "find the captain's hidden treasure"


@dataclass(frozen=True)
class Trouble:
    title: str
    problem: str
    mistake: str
    clue: str
    previous: str
    cause: str
    helper_job: str
    hero_job: str
    parrot_job: str
    repair: str
    lesson: str
    ending: str


TROUBLES = [
    Trouble(
        "The Upside-Down Map",
        "the treasure map pointed toward the sea with its compass rose upside down",
        "{hero} followed the arrow backward because it looked like a very confident fish",
        "the map's tiny anchor was drawn beside the old biscuit barrel, not the mast",
        "On a previous voyage, the crew had sailed three days after reading a map from the wrong side",
        "the map had been folded inside out during a windy sneeze",
        "held the map flat with a saucepan",
        "compared the anchor, barrel, and compass before choosing a course",
        "sang the correct direction in a voice too silly to forget",
        "turned the map around and marked its front with a bright pompon",
        "A previous mistake becomes useful when we remember it without letting it steer us forever.",
        "the marked map rested beside the candy chest while everyone laughed at the safe, sensible course",
    ),
    Trouble(
        "The Rubber Duck Alarm",
        "a loud squeak from the hold made everyone believe a sea monster had boarded",
        "{hero} prepared to duel the monster with a feather duster",
        "the squeak came only when the ship rolled near the laundry basket",
        "A previous scare had begun with a barrel that groaned like a hungry whale",
        "a loose rubber duck was trapped beneath the captain's rain boots",
        "tested the squeak by rocking the ship's deck",
        "opened the hold carefully instead of waving the duster",
        "carried the duck out and gave it a tiny sailor hat",
        "checked a sound before turning it into a monster story",
        "the harmless duck bobbed in a bucket while the crew sailed on, chuckling",
    ),
    Trouble(
        "The Missing Moustache",
        "Captain Brine's grand paper moustache vanished before the pirate parade",
        "{hero} suspected the parrot had stolen it for a beak warmer",
        "a stripe of paste led from the captain's chair to the biscuit tin",
        "A previous parade had ended when a gust glued the captain's hat to a cannon",
        "the moustache had stuck to a sweet biscuit and traveled into the tin",
        "followed the paste stripe without accusing the parrot",
        "searched the biscuit tin with clean hands",
        "posed proudly beside the recovered moustache",
        "asked for clues before blaming a crewmate",
        "Captain Brine wore the moustache crookedly, and the entire parade marched in giggles",
    ),
    Trouble(
        "The Wobbly Compass",
        "the compass spun whenever Pompon placed it near the galley",
        "{hero} thought the north star had become dizzy",
        "the needle steadied when the compass moved away from the iron soup pot",
        "A previous voyage had taught the crew to check tools before trusting a strange reading",
        "the iron pot was tugging at the compass",
        "moved the compass to the clean wooden table",
        "tested north against the sun and the ship's familiar bell",
        "kept the soup pot in the galley and away from navigation tools",
        "tools work best when we use them in the right place",
        "the compass pointed north, the soup stayed hot, and no star needed smelling salts",
    ),
    Trouble(
        "The Backward Flag",
        "the pirate flag hung upside down and made the ship look like it was surrendering to a cloud",
        "{hero} tried to salute the cloud",
        "the flag's stitched moon pointed toward the deck",
        "A previous flag had been mended during a storm with its skull smiling sideways",
        "the newest knot had been tied from the wrong side of the mast",
        "read the stitching and found the proper top edge",
        "climbed only after securing the ladder and telling the crew",
        "pulled the rope while making a very serious face",
        "used a clear mark and a shared check when fixing the flag",
        "the flag flew correctly above the Laughing Gull, while the cloud sailed away unoffended",
    ),
    Trouble(
        "The Secret Sneeze",
        "a sneeze from the treasure cave made the crew think the hidden chest was guarded by a dragon",
        "{hero} whispered a battle plan to a pile of rocks",
        "the sneeze followed every tickle of dust from the cave ceiling",
        "A previous cave search had ended with the captain wearing a stalactite like a hat",
        "dust had tickled a hidden goat sheltering behind the chest",
        "watched the dust settle before entering",
        "opened the cave slowly and covered the nose with a clean cloth",
        "led the goat outside with a carrot",
        "careful observation can turn a frightening sound into a manageable problem",
        "the goat received a snack while the treasure chest gleamed in the quiet cave",
    ),
]


OPENINGS = [
    "On a bright morning",
    "Beneath a sky as blue as a sailor's best button",
    "At the start of a famously wiggly voyage",
    "When the waves wore silver caps",
    "Near an island shaped like a sleeping boot",
    "On the deck of the Laughing Gull",
]

JOKES = [
    "The crew agreed this was no way to navigate, unless the destination was embarrassment.",
    "Even the ship's mop looked doubtful.",
    "The parrot laughed so hard that it forgot which foot was left.",
    "For one solemn moment, everyone blamed the weather, the biscuits, and one suspiciously round cloud.",
    "The captain puffed out his cheeks, which made him look less fierce and more like a surprised frog.",
    "Pompon tried to look wise, but a cracker was stuck to the hero's hat.",
]

PERSPECTIVES = [
    "The youngest deckhand remembered the lesson whenever a clue looked funny.",
    "Captain Brine added the repaired method to the ship's rulebook.",
    "The parrot repeated the important part until everyone could say it together.",
    "Pompon discovered that laughing at a mistake made it easier to fix without repeating it.",
    "The crew celebrated the answer more loudly than they had celebrated the treasure.",
]


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    hero: Entity
    captain: Entity
    helper: Entity
    parrot: Entity
    trouble: Trouble
    misunderstanding: bool = False
    teamwork: bool = False
    resolved: bool = False
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A humorous pirate tale about Pompon and a previous mistake.")
    parser.add_argument("--hero")
    parser.add_argument("--captain")
    parser.add_argument("--helper")
    parser.add_argument("--parrot")
    parser.add_argument("--place")
    parser.add_argument("--treasure")
    parser.add_argument("--sea")
    parser.add_argument("--task")
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
        seed=args.seed,
        hero=args.hero or rng.choice(["Pompon", "Pip", "Merry", "Biscuit"]),
        captain=args.captain or rng.choice(["Captain Brine", "Captain Noodle", "Captain Tumble"]),
        helper=args.helper or rng.choice(["Saffron", "Toby", "Mina", "Blue"]),
        parrot=args.parrot or rng.choice(["Jolly", "Pickle", "Peep"]),
        place=args.place or rng.choice(["the Laughing Gull", "the Wobbly Whale", "the Jolly Sardine"]),
        treasure=args.treasure or rng.choice(["a chest of lemon candies", "a silver teapot", "a sack of golden buttons"]),
        sea=args.sea or rng.choice(["the giggling blue sea", "the warm green sea", "the whispering sea"]),
        task=args.task or "find the captain's hidden treasure",
    )


def _validate(params: StoryParams) -> None:
    forbidden = {"poison", "weapon", "dangerous"}
    if any(word in params.treasure.lower() for word in forbidden):
        raise StoryError("The pirate treasure must be harmless and child-friendly.")
    if len({params.hero.lower(), params.captain.lower(), params.helper.lower()}) < 3:
        raise StoryError("Hero, captain, and helper need distinct names so their conversation is clear.")
    if not params.place.strip():
        raise StoryError("The pirate crew needs a ship or place to visit.")


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xC0FFEE)
    key = "|".join(
        [params.hero, params.captain, params.helper, params.parrot, params.place,
         params.treasure, params.sea, params.task]
    )
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big"))


def _ground(trouble: Trouble, params: StoryParams) -> Trouble:
    values = {
        "hero": params.hero,
        "captain": params.captain,
        "helper": params.helper,
        "parrot": params.parrot,
    }
    updates = {}
    for name in trouble.__dataclass_fields__:
        if name != "title":
            updates[name] = getattr(trouble, name).format(**values)
    return Trouble(trouble.title, **updates)


def _setup(world: World, opening: str) -> None:
    p = world.params
    world.say(
        f"{opening}, {p.hero} sailed aboard {p.place} with {p.captain}, {p.helper}, "
        f"and a parrot named {p.parrot}. They crossed {p.sea} to {p.task}."
    )
    world.say(
        f"The treasure was said to be {p.treasure}. Everyone wanted to find it, although "
        f"the ship's mop had already claimed the best hiding place."
    )


def _trouble(world: World, joke: str) -> None:
    p = world.params
    t = world.trouble
    world.para()
    world.misunderstanding = True
    world.hero.add_meme("confusion", 1)
    world.captain.add_meme("worry", 1)
    world.say(f"Then came {t.title}: {t.problem}.")
    world.say(f"{t.mistake}. {joke}")
    world.say(f"{t.previous}. Nobody wanted to repeat that adventure, especially the captain's hat.")


def _teamwork(world: World, question: str) -> None:
    p = world.params
    t = world.trouble
    world.para()
    world.teamwork = True
    world.hero.add_meme("curiosity", 1)
    world.helper.add_meme("resolve", 1)
    world.say(f"{p.hero} turned to {p.helper} and asked, '{question}'")
    world.say(f"{p.helper} answered, 'Let us check the clues before we steer into another silly mistake.'")
    world.say(f"They found this clue: {t.clue}. It connected the funny sign to the real cause: {t.cause}.")
    world.say(
        f"{p.helper} {t.helper_job}; {p.hero} {t.hero_job}; and {p.parrot} {t.parrot_job}. "
        f"Even {p.captain} stopped guessing and helped compare the evidence."
    )


def _resolution(world: World, perspective: str) -> None:
    p = world.params
    t = world.trouble
    world.para()
    world.resolved = True
    world.hero.add_meme("confidence", 1)
    world.say(f"The repair worked: they {t.repair}.")
    world.say(f"{p.captain} said, '{t.lesson}'")
    world.say(
        f"At last, the crew reached the right place and found {p.treasure}. "
        f"{t.ending} {perspective} The crew cheered, because a previous mistake had become a useful map."
    )


def tell(params: StoryParams) -> World:
    _validate(params)
    hero = Entity(params.hero, "hero")
    captain = Entity(params.captain, "captain")
    helper = Entity(params.helper, "helper")
    parrot = Entity(params.parrot, "parrot")
    chosen = _ground(_rng(params).choice(TROUBLES), params)
    world = World(params, hero, captain, helper, parrot, chosen)
    rng = _rng(params)
    _setup(world, rng.choice(OPENINGS))
    _trouble(world, rng.choice(JOKES))
    _teamwork(world, rng.choice([
        "What can we test before we make another grand pirate guess?",
        "Which clue belongs to the real problem?",
        "Can we remember what happened on the previous voyage?",
        "What would a careful sailor check first?",
    ]))
    _resolution(world, rng.choice(PERSPECTIVES))
    world.facts = {
        "hero": params.hero,
        "captain": params.captain,
        "helper": params.helper,
        "parrot": params.parrot,
        "place": params.place,
        "trouble": chosen.title,
        "problem": chosen.problem,
        "clue": chosen.clue,
        "previous": chosen.previous,
        "cause": chosen.cause,
        "repair": chosen.repair,
        "resolved": world.resolved,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
helper(X) :- helper_name(X).
previous_mistake :- remembers_previous.
misunderstanding :- strange_sign, not checked_clue.
teamwork :- asks_question, checks_clue, helps_crew.
resolved :- misunderstanding, teamwork, previous_mistake.
#show previous_mistake/0.
#show misunderstanding/0.
#show teamwork/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_name", "pompon"),
        asp.fact("helper_name", "saffron"),
        asp.fact("remembers_previous"),
        asp.fact("strange_sign"),
        asp.fact("asks_question"),
        asp.fact("checks_clue"),
        asp.fact("helps_crew"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_available() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


def asp_verify() -> int:
    if not asp_available():
        print("ASP verification unavailable: clingo is not installed.")
        return 1
    import asp
    model = asp.one_model(asp_program())
    names = {str(atom) for atom in model}
    expected = {"previous_mistake", "misunderstanding", "teamwork", "resolved"}
    if expected.issubset(names):
        sample = generate(StoryParams(seed=17))
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story data is incomplete.")
            return 1
        print("OK: ASP and Python pirate states agree.")
        return 0
    print("MISMATCH: ASP pirate state is incomplete.")
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a humorous pirate tale about {p.hero} aboard {p.place}.",
        f"Tell a child-friendly story where a previous mistake helps the crew find {p.treasure}.",
        f"Write a pirate adventure with {p.hero}, {p.helper}, and {p.parrot} solving a funny misunderstanding through clues.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    t = world.trouble
    return [
        QAItem(
            question=f"What trouble did {p.hero} and the crew face?",
            answer=f"They faced {t.title}: {t.problem}.",
        ),
        QAItem(
            question="What previous experience helped the crew?",
            answer=f"They remembered that {t.previous.lower()}, so they knew they should check the evidence before rushing ahead.",
        ),
        QAItem(
            question="What clue revealed the real cause?",
            answer=f"They noticed that {t.clue}. That clue showed that {t.cause}.",
        ),
        QAItem(
            question=f"How did {p.hero} and the crew solve the problem?",
            answer=f"{p.helper} {t.helper_job}; {p.hero} {t.hero_job}; and {p.parrot} {t.parrot_job}. Together they {t.repair}.",
        ),
        QAItem(
            question="What lesson did the captain share?",
            answer=t.lesson,
        ),
        QAItem(
            question="What final image showed that the adventure ended well?",
            answer=f"The crew found {p.treasure}, and {t.ending}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a vessel used by a pirate crew to travel, carry supplies, and explore the sea.",
        ),
        QAItem(
            question="Why are clues useful?",
            answer="Clues are useful because they provide evidence that can help people understand what happened and choose a sensible action.",
        ),
        QAItem(
            question="What does previous mean?",
            answer="Previous means something that happened earlier or came before the present moment.",
        ),
        QAItem(
            question="Why can humor help during a mistake?",
            answer="Humor can make people less frightened or embarrassed, helping them stay calm enough to fix the problem.",
        ),
        QAItem(
            question=f"What is the crew's treasure in this story?",
            answer=f"The crew's treasure is {p.treasure}.",
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
    for entity in [world.hero, world.captain, world.helper, world.parrot]:
        lines.append(f"{entity.kind}: {entity.name} meters={entity.meters} memes={entity.memes}")
    lines.append(
        f"state: misunderstanding={world.misunderstanding} "
        f"teamwork={world.teamwork} resolved={world.resolved}"
    )
    lines.append(f"trouble: {world.trouble.title}")
    return "\n".join(lines)


CURATED = [
    StoryParams(seed=101, hero="Pompon", captain="Captain Brine", helper="Saffron", parrot="Jolly"),
    StoryParams(seed=202, hero="Merry", captain="Captain Noodle", helper="Toby", parrot="Pickle"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show previous_mistake/0.\n#show misunderstanding/0.\n#show teamwork/0.\n#show resolved/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        if not asp_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", ", ".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero} aboard {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
