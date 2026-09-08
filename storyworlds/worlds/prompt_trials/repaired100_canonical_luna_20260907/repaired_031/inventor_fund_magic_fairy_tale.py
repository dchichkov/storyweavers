#!/usr/bin/env python3
"""
Standalone story world: an inventor, a small fund, and a little magic.

An inventive child dreams of building a helpful moon-lantern, but the purse
holding the project fund is nearly empty. A fairy offers a spark of magic with
one condition: the invention must be used for someone else before it can shine.
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
class Setting:
    id: str
    place: str
    affordances: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    inventor_name: str
    inventor_gender: str
    helper_name: str
    helper_kind: str
    fund_size: int
    invention: str
    setting: str
    magic: str
    opening_variant: int = 0
    turn_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "moonlit_workshop": Setting(
        "moonlit_workshop",
        "a moonlit workshop at the edge of the kingdom",
        {"inventing", "repairing", "sharing"},
    ),
    "whispering_tower": Setting(
        "whispering_tower",
        "an old tower above the whispering forest",
        {"inventing", "watching", "sharing"},
    ),
    "cobblestone_village": Setting(
        "cobblestone_village",
        "a little village of crooked chimneys",
        {"inventing", "repairing", "sharing"},
    ),
}

INVENTIONS = {
    "moon_lantern": {
        "label": "moon-lantern",
        "materials": ["silver wire", "blue glass", "a brass gear"],
        "purpose": "guide travelers home through dark woods",
    },
    "rainbell": {
        "label": "rainbell",
        "materials": ["tin", "a willow string", "a bell-shaped shell"],
        "purpose": "warn villagers when the river begins to rise",
    },
    "kindness_clock": {
        "label": "kindness clock",
        "materials": ["wooden wheels", "a red thread", "a pearl button"],
        "purpose": "remind busy people to stop and help one another",
    },
}

MAGICS = {
    "fairy_spark": {
        "label": "a fairy's silver spark",
        "effect": "makes a sincere invention glow",
        "condition": "it must be used to help someone before it can keep its light",
    },
    "singing_dew": {
        "label": "singing dew from a blue flower",
        "effect": "wakes sleeping gears with a bright little song",
        "condition": "the song fades if its maker keeps all the credit",
    },
    "star_thread": {
        "label": "a thread pulled from a falling star",
        "effect": "ties broken parts together without a knot",
        "condition": "it loosens when someone is forgotten",
    },
}

NAMES_GIRL = ["Luna", "Mira", "Iris", "Nell", "Tala"]
NAMES_BOY = ["Finn", "Theo", "Oren", "Milo", "Pip"]
HELPERS = [
    ("Grandmother", "elder"),
    ("Pip", "friend"),
    ("the village baker", "neighbor"),
    ("a young fairy", "fairy"),
]

OPENINGS = [
    "{inventor} lived in {setting}, where every loose screw seemed to whisper a question.",
    "On a silver evening, {inventor} opened the shutters of a workshop in {setting}.",
    "Long ago, in {setting}, {inventor} was known as the kingdom's smallest inventor.",
]

TURNS = [
    "The fund bought enough pieces for one final try, but not enough for a second mistake.",
    "When the last coin rang on the table, the invention still would not move.",
    "A cold wind swept through the workshop, and the nearly finished invention went dark.",
]

ENDINGS = [
    "From that night onward, the invention shone brightest whenever it was used for another.",
    "The kingdom remembered the invention, but it remembered the generous choice even more.",
    "And whenever a new problem appeared, {inventor} first asked whom the solution could help.",
]


def valid_combo(setting: str, invention: str, magic: str, fund_size: int) -> bool:
    return (
        setting in SETTINGS
        and invention in INVENTIONS
        and magic in MAGICS
        and 1 <= fund_size <= 7
    )


def explain_rejection(setting: str, invention: str, magic: str, fund_size: int) -> str:
    return (
        f"No story: setting={setting}, invention={invention}, magic={magic}, "
        f"fund={fund_size} does not describe a workable fairy-tale project."
    )


def _pronoun(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def tell(params: StoryParams) -> World:
    if not valid_combo(params.setting, params.invention, params.magic, params.fund_size):
        raise StoryError(
            explain_rejection(
                params.setting, params.invention, params.magic, params.fund_size
            )
        )

    setting = SETTINGS[params.setting]
    invention = INVENTIONS[params.invention]
    magic = MAGICS[params.magic]
    world = World(setting)

    inventor = world.add(
        Entity(
            "inventor",
            "character",
            params.inventor_name,
            meters={"coins": float(params.fund_size), "unfinished": 1.0},
            memes={"hope": 1.0, "pride": 1.0},
        )
    )
    helper = world.add(Entity("helper", "helper", params.helper_name, memes={"care": 1.0}))
    fairy = world.add(Entity("fairy", "magical_helper", "the young fairy", memes={"wonder": 1.0}))
    fund = world.add(
        Entity(
            "fund",
            "resource",
            "the project fund",
            meters={"coins": float(params.fund_size)},
        )
    )
    device = world.add(
        Entity(
            "device",
            "invention",
            invention["label"],
            meters={"parts": 0.0, "light": 0.0},
        )
    )

    pronoun = _pronoun(params.inventor_gender)
    possessive = _pronoun(params.inventor_gender, "possessive")
    materials = ", ".join(invention["materials"])

    opening = OPENINGS[params.opening_variant % len(OPENINGS)].format(
        inventor=params.inventor_name, setting=setting.place
    )
    world.say(opening)
    world.say(
        f"{params.inventor_name} was an inventor with {params.fund_size} bright coins "
        f"in a small project fund. {pronoun.capitalize()} hoped to build a "
        f"{invention['label']} from {materials}."
    )
    world.say(
        f"The invention would {invention['purpose']}, but {possessive} fund was "
        f"too small for wasteful guesses."
    )

    world.para()
    world.say(
        f"At midnight, {magic['label']} drifted through the window and settled on "
        f"the unfinished {invention['label']}."
    )
    world.say(
        f'"I can help," said the fairy. "My magic {magic["effect"]}, but {magic["condition"]}."'
    )
    world.say(
        f'"Then I will build it for the kingdom," said {params.inventor_name}. '
        f'"Not only for my name."'
    )
    world.facts["magic_offered"] = True
    world.fired.add(("magic", params.magic))
    fairy.memes["trust"] = 1.0

    world.para()
    world.say(TURNS[params.turn_variant % len(TURNS)])
    world.say(
        f"{params.inventor_name} counted the fund and chose the strongest pieces. "
        f"{pronoun.capitalize()} used the final coin to buy one tiny brass pin."
    )
    inventor.meters["coins"] = 0.0
    fund.meters["coins"] = 0.0
    device.meters["parts"] = 1.0
    inventor.memes["worry"] = 1.0
    world.say(
        f'The device gave a weak click. "It needs one more thing," whispered '
        f"{params.helper_name}."
    )
    world.say(
        f'"It needs a reason," said the fairy. "Who will be helped first?"'
    )
    world.say(
        f"{params.inventor_name} remembered a lost traveler waiting beyond the "
        f"forest and turned the invention toward the dark road."
    )
    world.facts["beneficiary"] = "a lost traveler"
    world.facts["decision"] = "share the invention before claiming credit"

    world.para()
    world.say(
        f"{params.inventor_name} placed {possessive} hands around the unfinished "
        f"{invention['label']} and said, "
        f'"Let its first light belong to whoever needs it."'
    )
    device.meters["light"] = 1.0
    device.meters["parts"] = 2.0
    inventor.memes["generosity"] = 1.0
    inventor.memes["hope"] = 2.0
    world.fired.add(("help", "lost_traveler"))
    world.say(
        f"The {invention['label']} sprang awake. Its gentle glow led a lost traveler "
        f"out of the forest and back to the village gate."
    )
    world.say(
        f'"You made it shine," said {params.helper_name}. '
        f'"No," replied {params.inventor_name}, smiling. '
        f'"The helping did."'
    )
    helper.memes["joy"] = 1.0
    world.facts["resolved"] = True

    world.para()
    world.say(
        ENDINGS[params.ending_variant % len(ENDINGS)].format(
            inventor=params.inventor_name
        )
    )
    world.say(
        f"The empty fund no longer looked sad. It had become the first chapter of "
        f"{params.inventor_name}'s greatest invention: a useful idea shared with care."
    )

    world.facts.update(
        inventor=inventor,
        helper=helper,
        fairy=fairy,
        fund=fund,
        device=device,
        invention=invention,
        magic=magic,
        materials=materials,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a fairy tale about an inventor whose small fund is tested by a magical invention.",
        f"Tell how {f['inventor'].id} uses {f['magic']['label']} and chooses to help {f['beneficiary']} before seeking credit.",
        f"Write a child-friendly ending in which the {f['device'].label} proves that generosity made the invention work.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    inventor = f["inventor"]
    helper = f["helper"]
    device = f["device"]
    return [
        QAItem(
            question=f"What kind of work did {inventor.label} do?",
            answer=f"{inventor.label} was an inventor who built a {device.label} from a small project fund.",
        ),
        QAItem(
            question="Why was the fund important?",
            answer=f"The fund held only {int(f['fund'].meters['coins'])} coins, so the inventor had to choose materials carefully and could not waste the last coin.",
        ),
        QAItem(
            question="What did the magic require?",
            answer=f"The magic required the invention to be used to help someone before it could keep its power.",
        ),
        QAItem(
            question="How did the inventor make the invention work?",
            answer=f"The inventor dedicated the first light to a lost traveler instead of keeping the invention only for personal credit, and the {device.label} awakened.",
        ),
        QAItem(
            question=f"What did {helper.label} learn or say at the end?",
            answer=f"{helper.label} noticed that the invention shone because the inventor chose to help someone, not because the inventor had a large fund.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inventor?",
            answer="An inventor is a person who creates a new tool, machine, or idea to solve a problem.",
        ),
        QAItem(
            question="What is a fund?",
            answer="A fund is money or another resource saved for a particular purpose.",
        ),
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic in a fairy tale is an extraordinary power that can change what ordinary people or objects are able to do.",
        ),
        QAItem(
            question="Why should a builder test an invention carefully?",
            answer="Careful testing helps a builder find mistakes and make sure the invention is safe and useful.",
        ),
        QAItem(
            question="What does generosity mean?",
            answer="Generosity means willingly sharing time, help, belongings, or credit with someone else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
magic_supports(inventor, invention) :- magic_offered, invention(invention).
can_complete(inventor, invention) :- magic_supports(inventor, invention), shares_with_someone(inventor).
good_story(setting, invention, magic) :-
    place(setting),
    invention(invention),
    magic(magic),
    magic_offered,
    shares_with_someone(inventor),
    can_complete(inventor, invention).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for iid in INVENTIONS:
        lines.append(asp.fact("invention", iid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    lines.extend(
        [
            asp.fact("magic_offered"),
            asp.fact("shares_with_someone", "inventor"),
            asp.fact("invention", "invention"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    import asp

    py = sorted((s, i, m) for s in SETTINGS for i in INVENTIONS for m in MAGICS)
    clingo_rows = asp_valid_combos()
    if set(py) == set(clingo_rows):
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", py)
    print("clingo:", clingo_rows)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale world of an inventor, a small fund, and magic."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--invention", choices=INVENTIONS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--fund", type=int)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper_name, helper_kind = rng.choice(HELPERS)
    if args.helper:
        helper_name = args.helper
    setting = args.setting or rng.choice(list(SETTINGS))
    invention = args.invention or rng.choice(list(INVENTIONS))
    magic = args.magic or rng.choice(list(MAGICS))
    fund = args.fund if args.fund is not None else rng.randint(2, 6)
    if not valid_combo(setting, invention, magic, fund):
        raise StoryError(explain_rejection(setting, invention, magic, fund))
    return StoryParams(
        inventor_name=name,
        inventor_gender=gender,
        helper_name=helper_name,
        helper_kind=helper_kind,
        fund_size=fund,
        invention=invention,
        setting=setting,
        magic=magic,
        opening_variant=rng.randrange(len(OPENINGS)),
        turn_variant=rng.randrange(len(TURNS)),
        ending_variant=rng.randrange(len(ENDINGS)),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.kind:14}) meters={meters} memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            "Luna",
            "girl",
            "Grandmother",
            "elder",
            3,
            "moon_lantern",
            "moonlit_workshop",
            "fairy_spark",
        ),
        StoryParams(
            "Finn",
            "boy",
            "Pip",
            "friend",
            4,
            "rainbell",
            "cobblestone_village",
            "singing_dew",
        ),
        StoryParams(
            "Mira",
            "girl",
            "the village baker",
            "neighbor",
            2,
            "kindness_clock",
            "whispering_tower",
            "star_thread",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        status = asp_verify()
        if status == 0:
            for params in curated_params():
                generate(params)
            print("OK: generated stories exercised.")
        sys.exit(status)
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        seen: set[str] = set()
        for index in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + index
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
            if sample.story not in seen:
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
            p = sample.params
            header = f"### {p.inventor_name}: {p.invention} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
