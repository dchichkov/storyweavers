#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about toil, a wand, and an assed mystery solved
through teamwork and a little humor.
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
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Pip"
    donkey: str = "Dabble"
    place: str = "the crooked village lane"
    wand: str = "a willow wand"
    task: str = "sweep the moonlit lane"
    prize: str = "a silver bell"


@dataclass(frozen=True)
class Mystery:
    title: str
    trouble: str
    guess: str
    clue: str
    silly_attempt: str
    cause: str
    helper_job: str
    hero_job: str
    donkey_job: str
    repair: str
    lesson: str
    ending: str


MYSTERIES = [
    Mystery(
        "The Vanishing Broom",
        "the broom vanished whenever the sweeping began",
        "the wand had whisked it away to the moon",
        "small straw marks curled toward the old water pump",
        "they searched the clouds and asked a sleepy star for directions",
        "Dabble had tucked the broom beneath his hay-filled cart for a cozy pillow",
        "followed the straw marks and checked behind the cart",
        "used the wand only to lift the heavy cart handle",
        "brayed an apology and pulled the broom free",
        "swept the lane in a bright circle",
        "A funny guess can be harmless, but a careful clue solves the case.",
        "the lane shone clean while Dabble wore the broom like a jaunty tail",
    ),
    Mystery(
        "The Backward Footprints",
        "backward hoofprints led from the well to the village bell",
        "a backwards ghost had marched through town",
        "the prints grew deeper beside a pile of spilled oats",
        "they walked backward too and bumped into a cabbage cart",
        "Dabble had backed up while eating oats from the ground",
        "measured the prints from the well to the bell",
        "held the wand above the ground so no one tripped",
        "pointed to the oats and demonstrated the hungry retreat",
        "gathered the oats and cleared the bell path",
        "When a mystery looks magical, ordinary evidence may still explain it.",
        "the bell rang forward as Dabble marched proudly beside the cleaned path",
    ),
    Mystery(
        "The Assed-Up Sign",
        "a sign reading 'ALL WORK ASSED' hung crookedly over the lane",
        "a secret spell had changed the village rules",
        "fresh hoof hair clung to the sign's lower edge",
        "they bowed to the sign and began doing every job backward",
        "Dabble had rubbed against the sign and knocked letters loose",
        "read the remaining letters aloud",
        "steadied the sign with the wand's gentle glow",
        "stood beneath it and admitted the accidental bump",
        "rewrote the sign as 'ALL WORK ASSIGNED'",
        "Clear words help a team know what job belongs to whom.",
        "the repaired sign swung straight while everyone laughed at the assed-up mistake",
    ),
    Mystery(
        "The Wandless Spark",
        "the willow wand stopped sparkling during the evening toil",
        "the wand had lost its magic because the job was too dull",
        "a dusty cobweb covered its tiny star-shaped tip",
        "they complimented the wand until it blushed and sneezed glitter",
        "the wand was simply dusty, not disappointed",
        "held the lantern close for a careful look",
        "brushed the cobweb away with a clean feather",
        "waved his tail and scattered the dust into a comic cloud",
        "cleaned the wand and used it to light the lane",
        "Tools work best when people inspect and care for them.",
        "the wand twinkled again, and Dabble sneezed one final silver sneeze",
    ),
    Mystery(
        "The Missing Rake",
        "the garden rake disappeared before the team could finish the toil",
        "a tiny rake thief had stolen it for a royal parade",
        "three neat lines crossed the soft mud toward the bakery",
        "they marched in a parade behind an empty bucket",
        "the baker had borrowed the rake to rescue a fallen flour sack",
        "followed the lines and asked the baker a kind question",
        "used the wand to gather the loose flour safely",
        "pulled the rake home after finishing his snack",
        "returned the rake and raked the lane together",
        "Asking kindly is faster than inventing a grand accusation.",
        "floury rake marks made a silver pattern beneath the morning sun",
    ),
    Mystery(
        "The Winking Lantern",
        "the lantern winked three times whenever someone lifted the wand",
        "the lantern was warning them about an invisible troll",
        "the wick bent each time the cold wind puffed through the gate",
        "they hid behind a barrel and challenged the troll to a staring contest",
        "the wind made the loose wick lean against the glass",
        "watched the lantern while the others moved the gate",
        "held the wand still and tested the flame",
        "closed the gate with his nose and made a proud little snort",
        "trimmed the wick and latched the gate",
        "A repeated pattern can turn a spooky sign into a simple answer.",
        "the lantern glowed steadily while Dabble winked at it first",
    ),
    Mystery(
        "The Stolen Prize",
        "the silver bell meant for the cleanest lane could not be found",
        "someone had hidden the prize to spoil the team effort",
        "a bright thread led from the prize shelf to Dabble's stall",
        "they searched every pocket and found only a button and a biscuit crumb",
        "Dabble had carried the bell away because its jingle sounded like supper",
        "followed the thread and listened near the stall",
        "used the wand to brighten the dark corner",
        "returned the bell after one last hopeful bray",
        "hung the prize where the whole team could ring it",
        "Shared work deserves shared credit, even when a donkey wants the applause.",
        "the silver bell rang above four smiling workers",
    ),
    Mystery(
        "The Muddy Moon",
        "a muddy moon shape appeared in the middle of the freshly swept lane",
        "the moon had fallen down and needed magical repair",
        "a wet hoof-shaped edge circled the mark",
        "they tried to lift the moon with the wand and nearly lifted a bucket",
        "Dabble had stepped in a puddle and stamped beside the clean path",
        "compared the mark with Dabble's hoof",
        "used the wand to guide clean sand over the mud",
        "stood still as a statue until the lane dried",
        "filled the puddle and swept the last muddy crescent away",
        "Wonder makes work lively, but evidence tells us what truly happened.",
        "a painted moon sign shone above a lane free of muddy footprints",
    ),
    Mystery(
        "The Chattering Gate",
        "the old gate chattered whenever the team carried a tool through it",
        "the gate had become a gossip who knew every village secret",
        "one loose hinge squeaked only when the wand passed",
        "they asked the gate who had borrowed the missing bucket",
        "the hinge needed oil, and the wand's metal tip made it squeak",
        "held the gate open while the hinge was examined",
        "oiled the hinge and tested the gate gently",
        "leaned against the gate and made it chatter once more",
        "oiled the hinge and carried the tools through quietly",
        "Listening closely can separate a useful signal from a funny noise.",
        "the gate swung silently as the team carried home the shining bucket",
    ),
    Mystery(
        "The Three Dusty Hats",
        "three dusty hats appeared on the workbench after the toil",
        "three invisible workers had joined the team",
        "the hats matched the shapes of the storage hooks",
        "they thanked the hats and offered them tiny cups of tea",
        "the hats had fallen from the hooks when Dabble bumped the bench",
        "matched each hat to its hook",
        "used the wand to lift the dust without scattering it",
        "nudged the bench back with one careful hoof",
        "cleaned the hats and fixed the loose hooks",
        "A strange scene becomes less strange when we check where things belong.",
        "the three hats rested neatly on their hooks while the team shared tea",
    ),
]


OPENINGS = [
    "By the bend of the village lane",
    "Where the blue hill met the rain",
    "In a town with chimneys bright",
    "At the edge of the garden gate",
    "Under a round and butter-yellow moon",
    "Before the sleepy stars came out",
    "In a lane both lumpy and long",
    "Beside a brook that hummed a song",
]

QUIPS = [
    "Aha! Let us inspect before we invent a dragon.",
    "A clue may be small, but it can wear a very loud hat.",
    "Let us ask the question before blaming the nearest hoof.",
    "Three pairs of eyes beat one very puzzled nose.",
    "We shall solve this neatly, and preferably without falling in a bucket.",
    "A mystery needs teamwork, not just dramatic pointing.",
]

TEAMWORK_LINES = [
    "They split the toil into little jobs and named each one aloud.",
    "They made a plan on a scrap of bark and checked it twice.",
    "One watched, one searched, and one held the tools steady.",
    "They lined the clues beside the path before choosing what to do.",
    "They traded jobs when a task grew heavy.",
    "They counted each step together, so no clue wandered away.",
]

PERSPECTIVES = [
    "Luna remembered that patience could be brighter than a wand.",
    "Pip wrote the clue on a card for the next village mystery.",
    "Dabble decided that helping was better than hiding tools for naps.",
    "The villagers praised the team for laughing without laughing at one another.",
    "Everyone agreed that a clear plan made hard toil feel light.",
    "From then on, the village checked facts before chasing fanciful guesses.",
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
    helper: Entity
    donkey: Entity
    place: str
    mystery: Optional[Mystery] = None
    confused: bool = False
    teamwork: bool = False
    solved: bool = False
    toil_done: bool = False
    wand_used: bool = False
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme world of toil, a wand, and a mystery."
    )
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--donkey")
    parser.add_argument("--place")
    parser.add_argument("--wand")
    parser.add_argument("--task")
    parser.add_argument("--prize")
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
        hero=args.hero or rng.choice(["Luna", "Nell", "Milo", "Tess"]),
        helper=args.helper or rng.choice(["Pip", "Bo", "Fenn", "Wren"]),
        donkey=args.donkey or rng.choice(["Dabble", "Noodle", "Pickle"]),
        place=args.place or rng.choice(
            ["the crooked village lane", "the moon garden", "the cobbled square"]
        ),
        wand=args.wand or rng.choice(["a willow wand", "a hazel wand", "a red-tipped wand"]),
        task=args.task or rng.choice(
            ["sweep the moonlit lane", "mend the garden gate", "tidy the village square"]
        ),
        prize=args.prize or rng.choice(["a silver bell", "a ribboned carrot", "a golden button"]),
    )


def validate(params: StoryParams) -> None:
    forbidden = {"poison", "dangerous", "broken", "empty"}
    for label, value in (
        ("hero", params.hero),
        ("helper", params.helper),
        ("donkey", params.donkey),
        ("place", params.place),
        ("wand", params.wand),
        ("task", params.task),
        ("prize", params.prize),
    ):
        if not value or not value.strip():
            raise StoryError(f"The {label} must not be empty.")
        if value.lower().strip() in forbidden:
            raise StoryError(f"The {label} must describe a gentle nursery-rhyme world.")
    if params.hero.lower() == params.helper.lower():
        raise StoryError("The hero and helper need different names so their teamwork is clear.")
    if params.hero.lower() == params.donkey.lower():
        raise StoryError("The donkey needs a different name from the hero.")


def stable_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xA551ED)
    key = "|".join(
        [
            params.hero,
            params.helper,
            params.donkey,
            params.place,
            params.wand,
            params.task,
            params.prize,
        ]
    )
    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def setup(world: World, opening: str) -> None:
    p = world.params
    world.say(
        f"{opening}, {p.hero} and {p.helper} began their toil with a hop and a rhyme. "
        f"They promised to {p.task} before the first star could shine."
    )
    world.say(
        f"{p.donkey} carried {p.prize} in a little blue cart, while {p.hero} carried "
        f"{p.wand}. The wand was useful, but the best tool was their teamwork."
    )


def raise_mystery(world: World, mystery: Mystery) -> None:
    p = world.params
    world.para()
    world.confused = True
    world.hero.add_meme("curiosity", 1)
    world.helper.add_meme("worry", 1)
    world.donkey.add_meme("mischief", 1)
    world.say(f"Then came a mystery, as odd as a duck in a hat: {mystery.trouble}.")
    world.say(f"{mystery.guess.capitalize()}.")
    world.say(f"At first, {mystery.silly_attempt}. The work stopped, and the lane grew quiet.")


def solve_mystery(world: World, mystery: Mystery, quip: str, method: str) -> None:
    p = world.params
    world.para()
    world.teamwork = True
    world.hero.add_meme("resolve", 1)
    world.helper.add_meme("resolve", 1)
    world.donkey.add_meme("helpfulness", 1)
    world.say(f"{p.hero} said to {p.helper}, '{quip}'")
    world.say(f"{method} They searched carefully and found this clue: {mystery.clue}.")
    world.say(
        f"Together they discovered the cause: {mystery.cause}. "
        f"The mystery shrank from a giant giant to a small, giggling fact."
    )
    world.say(
        f"{p.helper} {mystery.helper_job}; {p.hero} {mystery.hero_job}; and "
        f"{p.donkey} {mystery.donkey_job}."
    )


def resolve_story(world: World, mystery: Mystery, perspective: str) -> None:
    p = world.params
    world.para()
    world.solved = True
    world.toil_done = True
    world.wand_used = True
    world.say(f"The team repaired the trouble: they {mystery.repair}.")
    world.say(
        f"Then the toil was done. The wand gave one gentle twinkle, the {p.prize} "
        f"gave one bright jingle, and every tired face wore a smile."
    )
    world.say(f"{_cap(p.helper)} said, '{mystery.lesson}'")
    world.say(
        f"At dusk, {mystery.ending}. {perspective} So the mystery was solved, "
        f"the teamwork was praised, and the rhyme danced home."
    )


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def tell(params: StoryParams) -> World:
    validate(params)
    world = World(
        params=params,
        hero=Entity(params.hero, "hero"),
        helper=Entity(params.helper, "helper"),
        donkey=Entity(params.donkey, "donkey"),
        place=params.place,
    )
    rng = stable_rng(params)
    mystery = rng.choice(MYSTERIES)
    world.mystery = mystery
    setup(world, rng.choice(OPENINGS))
    raise_mystery(world, mystery)
    solve_mystery(world, mystery, rng.choice(QUIPS), rng.choice(TEAMWORK_LINES))
    resolve_story(world, mystery, rng.choice(PERSPECTIVES))
    world.facts = {
        "hero": params.hero,
        "helper": params.helper,
        "donkey": params.donkey,
        "place": params.place,
        "wand": params.wand,
        "mystery": mystery.title,
        "trouble": mystery.trouble,
        "clue": mystery.clue,
        "cause": mystery.cause,
        "resolved": world.solved,
        "teamwork": world.teamwork,
        "toil_done": world.toil_done,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
helper(X) :- helper_name(X).
donkey(X) :- donkey_name(X).
mystery_to_solve :- trouble_seen, clue_checked.
teamwork :- asks_for_help, searches_together, shares_jobs.
resolved :- mystery_to_solve, teamwork, repair_made.
#show mystery_to_solve/0.
#show teamwork/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero_name", "luna"),
            asp.fact("helper_name", "pip"),
            asp.fact("donkey_name", "dabble"),
            asp.fact("trouble_seen"),
            asp.fact("clue_checked"),
            asp.fact("asks_for_help"),
            asp.fact("searches_together"),
            asp.fact("shares_jobs"),
            asp.fact("repair_made"),
        ]
    )


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

    model = asp.one_model(
        asp_program(
            "#show mystery_to_solve/0.\n"
            "#show teamwork/0.\n"
            "#show resolved/0."
        )
    )
    found = {str(atom) for atom in model}
    expected = {"mystery_to_solve", "teamwork", "resolved"}
    if expected <= found:
        sample = generate(StoryParams(seed=17))
        if not sample.world or not sample.world.solved or not sample.world.teamwork:
            print("MISMATCH: generated story did not resolve its mystery.")
            return 1
        print("OK: ASP and Python both reach a solved teamwork state.")
        return 0
    print("MISMATCH: ASP twin did not reach the expected state.")
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a nursery rhyme about {p.hero}, {p.helper}, and {p.donkey} solving a mystery.",
        f"Tell a funny teamwork story involving toil and {p.wand}.",
        f"Write a child-friendly rhyme where an assed-up mistake is repaired with clues and kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    mystery = world.mystery
    assert mystery is not None
    return [
        QAItem(
            question=f"What mystery interrupted {p.hero} and {p.helper}'s toil?",
            answer=f"The trouble was that {mystery.trouble}.",
        ),
        QAItem(
            question="What clue helped the team solve the mystery?",
            answer=f"They noticed that {mystery.clue}. This clue pointed to the real cause.",
        ),
        QAItem(
            question=f"How did {p.hero}, {p.helper}, and {p.donkey} work as a team?",
            answer=(
                f"{p.helper} {mystery.helper_job}; {p.hero} {mystery.hero_job}; and "
                f"{p.donkey} {mystery.donkey_job}. Their different jobs completed one repair."
            ),
        ),
        QAItem(
            question="How was the assed-up or funny mistake repaired?",
            answer=f"They learned that {mystery.cause}, and then they {mystery.repair}.",
        ),
        QAItem(
            question="What lesson did the characters learn?",
            answer=mystery.lesson,
        ),
        QAItem(
            question="What final image showed that the mystery was solved?",
            answer=f"At the end, {mystery.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share jobs and help one another reach the same goal.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzling situation that becomes clearer when people gather clues and reason together.",
        ),
        QAItem(
            question="What is toil?",
            answer="Toil is steady, sometimes tiring work done to finish a useful task.",
        ),
        QAItem(
            question=f"What is a wand in this story?",
            answer=f"The wand is a small tool that helps the team with gentle magic while they work in {p.place}.",
        ),
        QAItem(
            question="Why can humor help a team?",
            answer="Humor can make a tense moment gentler, as long as the team still listens carefully and repairs the problem.",
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
    lines = ["--- world trace ---"]
    for entity in [world.hero, world.helper, world.donkey]:
        lines.append(
            f"{entity.kind}: {entity.name} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        "state: "
        f"mystery={world.mystery.title if world.mystery else None} "
        f"teamwork={world.teamwork} solved={world.solved} toil_done={world.toil_done}"
    )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="Luna",
        helper="Pip",
        donkey="Dabble",
        place="the crooked village lane",
        wand="a willow wand",
        task="sweep the moonlit lane",
        prize="a silver bell",
    ),
    StoryParams(
        hero="Nell",
        helper="Wren",
        donkey="Noodle",
        place="the moon garden",
        wand="a hazel wand",
        task="mend the garden gate",
        prize="a ribboned carrot",
    ),
    StoryParams(
        hero="Milo",
        helper="Bo",
        donkey="Pickle",
        place="the cobbled square",
        wand="a red-tipped wand",
        task="tidy the village square",
        prize="a golden button",
    ),
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
        print(
            asp_program(
                "#show mystery_to_solve/0.\n"
                "#show teamwork/0.\n"
                "#show resolved/0."
            )
        )
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        if not asp_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp

        model = asp.one_model(
            asp_program(
                "#show mystery_to_solve/0.\n"
                "#show teamwork/0.\n"
                "#show resolved/0."
            )
        )
        print("ASP model:", ", ".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and attempt < limit:
            seed = base_seed + attempt
            attempt += 1
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
            header = f"### {sample.params.hero} and {sample.params.helper} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
