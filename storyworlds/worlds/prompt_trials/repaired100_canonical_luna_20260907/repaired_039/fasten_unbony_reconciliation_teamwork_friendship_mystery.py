#!/usr/bin/env python3
"""A child-friendly mystery about fastening an unbony friendship back together."""

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
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectItem:
    name: str
    label: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    friend: str = "Tavi"
    place: str = "the old clock tower"
    mystery: str = "the vanished silver clasp"
    token: str = "a moon-shaped friendship locket"


@dataclass(frozen=True)
class Case:
    key: str
    clue: str
    false_lead: str
    danger: str
    discovery: str
    repair: str
    ending: str
    lesson: str


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, ObjectItem] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Luna", "Mira", "Nora", "Ivo", "Sami", "Pia", "Theo", "Anya"]
FRIENDS = ["Tavi", "Milo", "Rin", "Bea", "Jules", "Kito", "Wren", "Omi"]
PLACES = [
    "the old clock tower",
    "the lantern museum",
    "the riverside station",
    "the quiet library",
    "the covered market",
]
MYSTERIES = [
    "the vanished silver clasp",
    "the missing brass key",
    "the lost blue button",
    "the secret note without its seal",
    "the lantern with a broken fastener",
]
TOKENS = [
    "a moon-shaped friendship locket",
    "a tiny compass badge",
    "a red ribbon medal",
    "a starry puzzle box",
    "a brass friendship pin",
]

CASES = [
    Case(
        "bell_rope",
        "A strand of blue thread was caught on the bell rope.",
        "A dusty footprint pointed toward the stairs.",
        "Pulling the loose rope could drop the clasp into the bell gears.",
        "The thread matched the ribbon on the mystery box, not either child's coat.",
        "Luna held the rope still while Tavi reached with a hooked umbrella and lifted the clasp free.",
        "They fastened the moon locket again and heard the tower bell ring once.",
        "Careful teamwork can reveal what a hurried guess hides.",
    ),
    Case(
        "rain_window",
        "Three dry drops marked a path beneath the only open window.",
        "A muddy shoeprint made it seem that a stranger had climbed inside.",
        "Rainwater was spreading toward the paper map that explained the mystery.",
        "The shoeprint stopped at the window, while a smaller trail led under a bench.",
        "Tavi covered the map while Luna followed the small trail and found the clasp in a drain cup.",
        "They dried the map, fastened the clasp, and watched the rain turn the window silver.",
        "A friend deserves questions before blame.",
    ),
    Case(
        "silent_clock",
        "The clock's minute hand had stopped beside the number twelve.",
        "A scratch on the case looked like a mark from a thief.",
        "The hidden catch was jammed, so forcing it might damage the old clock.",
        "The scratch was fresh wax from a candle, and the catch moved when the hand was gently lifted.",
        "Luna steadied the clock while Tavi loosened the wax with a warm cloth.",
        "The compartment opened, and the clasp shone beside a note asking them to listen to each other.",
        "Reconciliation begins when people make room for the whole truth.",
    ),
    Case(
        "market_box",
        "A row of buttons led from the display to a basket of cloth scraps.",
        "A torn label named Tavi as the last person near the display.",
        "The basket was balanced on a narrow shelf above a glass case.",
        "The buttons belonged to a costume repair, and the torn label had been cut by a loose hook.",
        "Tavi braced the shelf while Luna searched the cloth and found the clasp sewn inside a pocket.",
        "They returned the clasp and repaired the pocket together before closing time.",
        "Shared work can mend both an object and a friendship.",
    ),
    Case(
        "river_bridge",
        "A bright reflection blinked below the bridge rail.",
        "A note said, 'Trust no one,' in handwriting that looked like Luna's.",
        "Leaning over the rail could send either the token or a child into the river.",
        "The note used Luna's old spelling, but its ink was still wet; the reflection was only a metal washer.",
        "They tied a scarf to the rail, lowered a basket, and found the clasp safely caught in reeds.",
        "They fastened the token and tore up the false note side by side.",
        "Truth is stronger when friends test clues together.",
    ),
    Case(
        "library_ladder",
        "A tiny silver scrape curved from the ladder to a shelf of adventure books.",
        "A book about secret thieves lay open to a page about stolen treasures.",
        "The ladder wobbled beneath the high shelf where the clasp glimmered.",
        "The scrape came from the clasp sliding behind a book, and the open book had simply been left by a reader.",
        "Luna held the ladder while Tavi used a ruler to draw the clasp toward the edge.",
        "They fastened the locket and placed the adventure book back in its proper place.",
        "A shared view of the evidence is better than a dramatic story.",
    ),
]

OPENINGS = [
    "{hero} and {friend} met beneath the tall clock at {place}, carrying a small secret between them.",
    "At {place}, the morning fog curled around the stones as {hero} noticed something missing.",
    "The mystery began when {hero} opened the velvet case and found only an empty groove.",
    "Long before the first visitor arrived at {place}, {hero} and {friend} were searching the quiet rooms.",
]
ARGUMENTS = [
    '"You promised to keep it safe," {hero} said, touching the empty groove.',
    '"You were the last one holding the token," {hero} whispered.',
    '"I thought you blamed me," {friend} said, looking at the floor.',
    '"The mystery is hard enough without us guessing at each other," {friend} replied.',
]
RECONCILIATIONS = [
    '"I was frightened, not certain," {hero} admitted. "I am sorry."',
    '"I should have told you what happened," {friend} said. "Can we search as a team?"',
    '"Let us check every clue before we choose a culprit," {hero} said.',
    '"Friends can disagree and still help one another," {friend} answered.',
]
REFLECTIONS = [
    "The solved mystery felt good, but saying sorry made the friendship feel stronger.",
    "{hero} learned that trust was not a guess; it was something they rebuilt through actions.",
    "The answer had been hidden in plain sight, while their hurt had needed honest words.",
    "They had not only recovered a clasp. They had fastened their friendship to patience again.",
]


def make_world(params: StoryParams) -> World:
    if params.hero == params.friend:
        raise StoryError("hero and friend must be different people")
    world = World(params=params)
    hero = Person(params.hero, "detective")
    friend = Person(params.friend, "friend")
    token = ObjectItem("token", params.token, owner=params.hero)
    world.people = {hero.name: hero, friend.name: friend}
    world.items = {"token": token}
    world.facts.update(hero=hero, friend=friend, token=token, place=params.place)
    return world


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    case = rng.choice(CASES)

    world.say(rng.choice(OPENINGS).format(hero=params.hero, friend=params.friend, place=params.place))
    world.say(
        f"They had brought {params.token} to solve {params.mystery}, but its clasp was gone."
    )
    world.say(rng.choice(ARGUMENTS).format(hero=params.hero, friend=params.friend))
    world.para()
    world.say(case.danger)
    world.say(case.false_lead)
    world.say(f'Then {params.friend} pointed to a clue: "{case.clue}"')
    world.say(
        rng.choice(RECONCILIATIONS).format(hero=params.hero, friend=params.friend)
    )
    world.say(
        f"They agreed to use teamwork: {params.hero} would watch the safe path, and "
        f"{params.friend} would follow the evidence."
    )
    world.para()
    world.say(case.discovery)
    world.say(case.repair)
    world.say(
        f'The mystery was solved because they listened before deciding who was at fault.'
    )
    world.say(case.ending)
    world.say(rng.choice(REFLECTIONS).format(hero=params.hero, friend=params.friend))
    world.say(
        f'{params.friend} said, "The best clue was remembering that friendship needs care."'
    )
    world.say(f"{case.lesson} {case.ending}")

    world.people[params.hero].meters.update(attention=1.0, trust=0.9)
    world.people[params.friend].meters.update(care=1.0, trust=0.9)
    world.people[params.hero].memes.update(worry=0.2, reconciliation=1.0)
    world.people[params.friend].memes.update(worry=0.2, reconciliation=1.0)
    world.items["token"].meters.update(found=1.0, fastened=1.0)
    world.facts.update(
        case=case.key,
        clue=case.clue,
        false_lead=case.false_lead,
        danger=case.danger,
        discovery=case.discovery,
        repair=case.repair,
        ending=case.ending,
        lesson=case.lesson,
        resolved=True,
        reconciled=True,
        teamwork=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly mystery in which {p.hero} and {p.friend} recover {p.mystery}.",
        f"Show reconciliation, teamwork, and friendship through clues at {p.place}.",
        f"Use the words fasten and unbony in a gentle mystery about repairing trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    return [
        QAItem(
            f"What went missing at {p.place}?",
            f"The clasp from {p.token} went missing while {p.hero} and {p.friend} were preparing to solve {p.mystery}.",
        ),
        QAItem(
            "Why did the friends first feel upset with each other?",
            f"{p.hero} feared that {p.friend} had not kept the token safe, but the clue later showed that blaming a friend was not proof.",
        ),
        QAItem(
            "What clue helped solve the mystery?",
            f'{f["clue"]} That detail guided their search more reliably than the false lead: {f["false_lead"]}',
        ),
        QAItem(
            "How did teamwork help?",
            f"{p.hero} watched the safe path while {p.friend} followed the evidence, so they could solve the danger without rushing.",
        ),
        QAItem(
            "How did the friends reconcile?",
            f"They admitted they were frightened, apologized for guessing, and listened to the whole set of clues before repairing the token together.",
        ),
        QAItem(
            "What changed at the end?",
            f"The clasp was fastened again, and their friendship was strengthened because they replaced suspicion with honest teamwork.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does it mean to fasten something?",
            "To fasten something means to secure or join it so it stays in place, such as closing a clasp or tying a knot.",
        ),
        QAItem(
            "What does unbony mean in this story?",
            "Unbony is a playful story word meaning to soften a stiff, bony disagreement so people can move toward kindness and peace.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is the process of repairing a relationship after hurt or disagreement through honesty, listening, apology, and changed actions.",
        ),
        QAItem(
            "Why should detectives check clues before blaming someone?",
            "Clues can reveal what actually happened. Checking them prevents a guess from hurting an innocent person and helps everyone choose a safer solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
friend(F) :- friend_name(F).
token(T) :- token_name(T).
mystery_solved(H,F,T) :- hero(H), friend(F), token(T), clue_checked, teamwork, reconciled, fastened.
friendship_repaired(H,F) :- mystery_solved(H,F,_), reconciliation.
unbony_peace(H,F) :- friendship_repaired(H,F), listened.
#show mystery_solved/3.
#show friendship_repaired/2.
#show unbony_peace/2.
"""

DEFAULT_PARAMS = StoryParams()


def asp_facts() -> str:
    import asp

    p = DEFAULT_PARAMS
    return "\n".join(
        [
            asp.fact("hero_name", p.hero),
            asp.fact("friend_name", p.friend),
            asp.fact("token_name", p.token),
            asp.fact("clue_checked"),
            asp.fact("teamwork"),
            asp.fact("reconciled"),
            asp.fact("fastened"),
            asp.fact("reconciliation"),
            asp.fact("listened"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    atoms = asp.one_model(asp_program())
    solved = asp.atoms(atoms, "mystery_solved")
    repaired = asp.atoms(atoms, "friendship_repaired")
    peaceful = asp.atoms(atoms, "unbony_peace")
    if not (solved and repaired and peaceful):
        print("MISMATCH: ASP reconciliation model is incomplete.")
        return 1
    for seed in range(3):
        sample = generate(StoryParams(seed=seed))
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
    print("OK: ASP and Python agree on the fastened reconciliation mystery.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--token", choices=TOKENS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    if hero == friend:
        friend = rng.choice([name for name in FRIENDS if name != hero])
    return StoryParams(
        seed=args.seed,
        hero=hero,
        friend=friend,
        place=args.place or rng.choice(PLACES),
        mystery=args.mystery or rng.choice(MYSTERIES),
        token=args.token or rng.choice(TOKENS),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    if trace and sample.world:
        world = sample.world
        print(
            "\n--- trace ---\n"
            f"hero={world.params.hero}\n"
            f"friend={world.params.friend}\n"
            f"case={world.facts['case']}\n"
            f"clue={world.facts['clue']}\n"
            f"reconciled={world.facts['reconciled']}\n"
            f"teamwork={world.facts['teamwork']}\n"
            f"resolved={world.facts['resolved']}"
        )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        atoms = asp.one_model(asp_program())
        print("ASP model:")
        for name in ("mystery_solved", "friendship_repaired", "unbony_peace"):
            for atom in asp.atoms(atoms, name):
                print(f"{name}{atom}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, case in enumerate(CASES):
            params = StoryParams(
                seed=base_seed + i,
                hero=args.hero or NAMES[i % len(NAMES)],
                friend=args.friend or FRIENDS[i % len(FRIENDS)],
                place=args.place or PLACES[i % len(PLACES)],
                mystery=args.mystery or MYSTERIES[i % len(MYSTERIES)],
                token=args.token or TOKENS[i % len(TOKENS)],
            )
            if params.hero == params.friend:
                params.friend = FRIENDS[(i + 1) % len(FRIENDS)]
            samples.append(generate(params))
    else:
        for i in range(max(0, args.n)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
