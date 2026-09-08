#!/usr/bin/env python3
"""A nursery-rhyme storyworld about parody, bravery, and a reading nook."""

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
class Prop:
    name: str
    label: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Milo"
    setting: str = "the reading nook"
    rhyme: str = "The Cat and the Hat"
    parody: str = "The Cat with the Hat in a Hurry"
    lesson: str = "A brave voice asks for help before a small mistake grows."


@dataclass(frozen=True)
class Trial:
    key: str
    prop: str
    trouble: str
    clue: str
    bad_choice: str
    brave_choice: str
    helper_task: str
    repair: str
    consequence: str
    ending: str


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    props: dict[str, Prop] = field(default_factory=dict)
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


NAMES = ["Luna", "Mira", "Nell", "Pip", "Toby", "Ada"]
HELPERS = ["Milo", "Nora", "Grandma", "Ben", "Aunt Bea"]
SETTINGS = ["the reading nook", "the library corner", "the window-seat nook"]
RHYME_TITLES = ["The Cat and the Hat", "The Fox in Socks", "The Owl and the Pussy-Cat"]
PARODIES = [
    "The Cat with the Hat in a Hurry",
    "The Fox with Socks That Won't Stay Put",
    "The Owl Who Lost the Moonlit Map",
]
TRIALS = [
    Trial(
        "hat",
        "paper hat",
        "A blue paper hat slipped from the rhyme book and landed in the lamp.",
        "The lamp shade trembled whenever the hat's long feather brushed it.",
        "hide the hat behind the cushions and pretend nothing had happened",
        "tell the truth, even though her cheeks felt hot",
        "hold the book open and keep the lamp still",
        "Luna used a wooden ruler to guide the feather away while Milo lifted the hat by its dry brim.",
        "The lamp stayed safe, but the parody lost its silly hat until they folded a new one.",
        "A neat little hat stood beside the book, ready for a second reading.",
    ),
    Trial(
        "socks",
        "striped sock puppet",
        "A sock puppet sprang from the story basket and knocked over the rhyme cards.",
        "The cards with moon pictures were scattered nearest the puppet's tail.",
        "blame the draft and shove every card into one crooked pile",
        "say what she saw and sort the cards by their pictures",
        "make three clear piles for moon, fox, and road",
        "They matched each picture, then read the lines in their new order.",
        "The parody's joke returned, but one card had a bent corner from the hurried pile.",
        "The sock puppet bowed beside three tidy stacks of cards.",
    ),
    Trial(
        "moon",
        "silver moon bookmark",
        "The silver moon bookmark tore while Luna pulled it from a crowded book.",
        "Only the paper strip tore; its little silver moon stayed whole.",
        "pull harder and tuck the torn bookmark out of sight",
        "admit the tear and pause before making it worse",
        "fetch a strip of ribbon and a dab of paste",
        "They pasted the moon to ribbon and pressed it flat beneath a heavy book.",
        "The repaired bookmark worked, though its ribbon was shorter than before.",
        "The moon bookmark shone from the page like a tiny brave smile.",
    ),
    Trial(
        "tower",
        "tower of storybooks",
        "A tall stack of books leaned toward the soft chair.",
        "The heaviest book sat at the very top, where it made the tower wobble.",
        "snatch the top book and let the leaning stack tumble",
        "call for help and clear a safe space first",
        "steady the lower books while Luna moved the heavy one",
        "They rebuilt the tower from broad books below to slim books above.",
        "No one was hurt, but the old stack fell with a thump that ended the first reading.",
        "The new tower stood low and firm beneath the reading lamp.",
    ),
    Trial(
        "rhyme",
        "rhyme card",
        "A spilled cup made the final words on the parody card run together.",
        "The first half of each couplet was still dry beside the ink.",
        "rub the wet letters quickly and smear the whole rhyme",
        "protect the dry words and ask for a cloth",
        "blot the card from the edge without rubbing",
        "They dried the card, copied the missing words, and made a fresh rhyme.",
        "The parody became a little different, but its beat still danced.",
        "The new card rhymed on, bright and bold, beside the quiet books.",
    ),
]

OPENINGS = [
    "{hero} loved the hush of {setting}, where every book had a doorway and every page had a tune.",
    "By the lamp in {setting}, {hero} prepared a tiny show for the afternoon reading.",
    "In {setting}, where cushions were hills and shelves were trees, {hero} opened a favorite rhyme book.",
]
BRAVE_LINES = [
    '"I made a mistake," {hero} said. "I need help before it grows."',
    '"I am afraid to say it," {hero} whispered, "but hiding will not fix it."',
    '"Bravery can be a small true sentence," {hero} said, standing up straight.',
]
HELP_LINES = [
    '"Thank you for telling me," {helper} replied. "Now we can make a safe plan."',
    '"A brave voice gives helpers a chance to help," {helper} said.',
    '"We will fix what we can, one careful step at a time," {helper} promised.',
]
BAD_LINES = [
    "{hero} nearly chose silence, and the trouble grew louder in the little nook.",
    "For one breath, {hero} thought a hidden mistake might disappear.",
]
REFLECTIONS = [
    "The parody was funny, but the truest verse was the one {hero} spoke aloud.",
    "The rhyme had changed, yet its happy beat returned because courage made room for care.",
    "{hero} learned that bravery is not never being scared; it is telling the truth while scared.",
]


def make_world(params: StoryParams) -> World:
    world = World(params=params)
    hero = Person(params.hero, "hero")
    helper = Person(params.helper, "helper")
    book = Prop("rhyme_book", params.rhyme, params.hero)
    world.people = {hero.name: hero, helper.name: helper}
    world.props = {book.name: book}
    world.facts.update(hero=hero, helper=helper, book=book, setting=params.setting)
    return world


def generate_story_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different people")
    if params.setting not in SETTINGS:
        raise StoryError(f"unknown reading setting: {params.setting}")
    rng = random.Random(params.seed if params.seed is not None else 0)
    trial = rng.choice(TRIALS)
    world = make_world(params)
    p = params
    world.say(rng.choice(OPENINGS).format(hero=p.hero, setting=p.setting))
    world.say(
        f'{p.hero} had written a parody called "{p.parody}", '
        f"with a bouncy beat borrowed from {p.rhyme}."
    )
    world.say(f"The rhyme card waited beside the lamp, ready for {p.helper} to hear.")
    world.para()
    world.say(trial.trouble)
    world.say(rng.choice(BAD_LINES).format(hero=p.hero))
    world.say(f"Then {p.hero} noticed a clue: {trial.clue}")
    world.say(rng.choice(BRAVE_LINES).format(hero=p.hero))
    world.para()
    world.say(rng.choice(HELP_LINES).format(helper=p.helper))
    world.say(
        f"{p.hero} {trial.brave_choice}, while {p.helper} {trial.helper_task}."
    )
    world.say(trial.repair)
    world.say("They checked the nook together before opening the book again.")
    world.para()
    world.say(trial.consequence)
    world.say(rng.choice(REFLECTIONS).format(hero=p.hero))
    world.say(
        f'{p.helper} tapped the cover and said, "{p.lesson}"'
    )
    world.say(f"When the reading began, {trial.ending}")
    world.people[p.hero].memes.update(bravery=1.0, honesty=1.0, fear=0.2)
    world.people[p.helper].memes.update(care=1.0, trust=1.0)
    world.props["rhyme_book"].meters["safe"] = 1.0
    world.facts.update(
        trial=trial.key,
        prop=trial.prop,
        trouble=trial.trouble,
        clue=trial.clue,
        bad_choice=trial.bad_choice,
        brave_choice=trial.brave_choice,
        helper_task=trial.helper_task,
        repair=trial.repair,
        consequence=trial.consequence,
        ending=trial.ending,
        resolved=True,
        bad_ending_avoided=True,
        parody=p.parody,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a nursery-rhyme-style parody story about {p.hero} in {p.setting}.",
        f"Show {p.hero} using bravery to admit a problem while {p.helper} helps repair it.",
        f"Tell a child-friendly tale where a bad ending is avoided through honesty and care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    trouble = str(f["trouble"])
    clue = str(f["clue"])
    return [
        QAItem(
            f"What went wrong in {p.setting}?",
            f"In {p.setting}, {trouble[0].lower() + trouble[1:]} This put the parody reading at risk.",
        ),
        QAItem(
            "What clue did the characters notice?",
            f"They noticed that {clue[0].lower() + clue[1:]} The clue helped them choose a careful repair.",
        ),
        QAItem(
            f"How did {p.hero} show bravery?",
            f"{p.hero} showed bravery by {f['brave_choice']}. Telling the truth allowed {p.helper} to help.",
        ),
        QAItem(
            "How did the two characters solve the problem?",
            f"{p.hero} {f['brave_choice']}, while {p.helper} {f['helper_task']}. Then {f['repair']}",
        ),
        QAItem(
            "What prevented a bad ending?",
            f"They avoided a bad ending by stopping the risky choice, speaking honestly, and repairing the problem together. {f['ending']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a parody?",
            "A parody is a playful new work that imitates a familiar work while changing details for humor or a fresh idea.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery means doing what is right or useful even when fear makes the choice difficult. It can be as small as telling the truth and asking for help.",
        ),
        QAItem(
            "Why can asking for help prevent a bad ending?",
            "Asking for help lets another person notice danger, share the work, and make a safer plan before a small problem grows.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
reading_nook(S) :- setting(S).
parody(P) :- parody_title(P).
brave_choice(H) :- hero(H), admitted_problem(H).
helper_present(K) :- helper(K), offered_help(K).
bad_ending_avoided(H,K) :- brave_choice(H), helper_present(K), repaired.
complete_reading(H,K,P) :- bad_ending_avoided(H,K), parody(P).
"""

DEFAULT_PARAMS = StoryParams()


def asp_facts() -> str:
    import asp

    p = DEFAULT_PARAMS
    return "\n".join(
        [
            asp.fact("hero_name", p.hero),
            asp.fact("helper_name", p.helper),
            asp.fact("setting", p.setting),
            asp.fact("parody_title", p.parody),
            asp.fact("admitted_problem", p.hero),
            asp.fact("offered_help", p.helper),
            asp.fact("repaired"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(
        asp_program("#show complete_reading/3.")
    )
    atoms = asp.atoms(symbols, "complete_reading")
    if not atoms:
        print("MISMATCH: ASP did not derive a completed parody reading.")
        return 1
    params = StoryParams(seed=17)
    sample = generate(params)
    if not sample.story or "bravery" not in sample.story.lower():
        print("MISMATCH: generated story failed bravery check.")
        return 1
    print("OK: ASP and Python agree that bravery avoids the bad ending.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--rhyme", choices=RHYME_TITLES)
    parser.add_argument("--parody", choices=PARODIES)
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
    helper = args.helper or rng.choice([x for x in HELPERS if x != hero])
    return StoryParams(
        seed=args.seed,
        hero=hero,
        helper=helper,
        setting=args.setting or rng.choice(SETTINGS),
        rhyme=args.rhyme or rng.choice(RHYME_TITLES),
        parody=args.parody or rng.choice(PARODIES),
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
            f"helper={world.params.helper}\n"
            f"trial={world.facts['trial']}\n"
            f"bravery={world.people[world.params.hero].memes['bravery']}\n"
            f"bad_ending_avoided={world.facts['bad_ending_avoided']}\n"
            f"resolved={world.facts['resolved']}"
        )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show complete_reading/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show complete_reading/3."))
        print(asp.atoms(symbols, "complete_reading"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = len(TRIALS) if args.all else args.n
    for i in range(count):
        seed = base_seed + i
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
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
