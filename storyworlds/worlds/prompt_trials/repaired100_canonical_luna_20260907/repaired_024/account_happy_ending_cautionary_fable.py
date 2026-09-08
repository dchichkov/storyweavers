#!/usr/bin/env python3
"""
A cautionary fable about an account, a tempting shortcut, and a happy ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    trait: str
    village: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class FableArc:
    id: str
    temptation: str
    shortcut: str
    danger: str
    honest_action: str
    consequence: str
    repair: str
    moral: str
    final_image: str


NAMES = ["Luna", "Mira", "Nell", "Tavi", "Pia", "Rin"]
TRAITS = ["careful", "curious", "kind", "patient"]
VILLAGES = ["Willowbrook", "Cloverfield", "Mossy Hollow", "Sunseed"]
ARCS = [
    FableArc(
        "missing_coin",
        "a brass account book with one bright coin drawn on its last page",
        "copying a neighbor's mark so the book would show a larger balance",
        "the village trust would be broken when the false mark was found",
        "showed the book to the miller and told the truth about the missing coin",
        "The account could not be trusted while its bright page hid a lie.",
        "The miller helped search the path, and the coin was found beneath a buttercup.",
        "An honest account is worth more than a proud-looking total.",
        "At sunset, the true coin rested in the account book, and every mark on the page was clear.",
    ),
    FableArc(
        "borrowed_seed",
        "an account promising three golden seeds for every seed borrowed",
        "writing down three seeds before returning even one",
        "the garden would owe more than it could grow",
        "asked the gardener to count the seeds together",
        "The account grew quickly, but the little garden grew no seeds at all.",
        "The gardener found two seeds in Luna's pocket and planted them beside the last bean.",
        "A promise should be counted with care before it is accepted.",
        "Three green shoots rose beside the book, each paid for by a true seed.",
    ),
    FableArc(
        "lantern_debt",
        "a lantern seller's account that offered light today and payment tomorrow",
        "promising tomorrow's eggs for a lantern needed tonight",
        "the family henhouse would be empty before morning",
        "asked the seller for a smaller lantern she could pay for now",
        "The large lantern shone brightly, but its debt made Luna's worry grow.",
        "The seller exchanged it for a small lamp and erased the impossible promise.",
        "A bright bargain can cast a dark shadow when its cost is hidden.",
        "The small lamp glowed beside a full basket of eggs.",
    ),
    FableArc(
        "kindness_ledger",
        "a ledger that counted every kindness as a favor to be repaid",
        "recording a friend's help as a debt instead of a gift",
        "friendship would become a cold trade",
        "crossed out the debt and thanked her friend freely",
        "The ledger made every smile feel heavy and every favor feel borrowed.",
        "Her friend added a flower to the page and wrote, 'No payment needed.'",
        "Kindness loses its sweetness when it is measured like coins.",
        "The account became a garden of flowers, not a list of debts.",
    ),
]

OPENINGS = [
    "In a small village",
    "One clear morning in the village",
    "At the edge of a green valley",
    "When the market bell rang",
]
DIALOGUE_REQUESTS = [
    "Can you help me read this account?",
    "What should I do before I write anything?",
    "Is this bargain really as good as it looks?",
    "May we count it together?",
]
REFLECTIONS = [
    "Luna had wanted the easy answer, but the truth made a safer path.",
    "The page had looked clever; the honest choice made it useful.",
    "A small confession opened a larger door than a hidden mark ever could.",
    "The mistake became a lesson because Luna did not protect it with another mistake.",
]

ASP_RULES = r"""
honest(hero) :- tells_truth(hero).
safe_account(A) :- account(A), honest(hero).
happy_ending :- safe_account(account).
#show honest/1.
#show safe_account/1.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("account", "account"),
        asp.fact("tells_truth", "hero"),
    ])


def asp_program(show: str = "#show happy_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {atom.name for atom in model}
    if "happy_ending" not in names:
        print("MISMATCH: ASP did not derive the happy ending.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "happy ending" not in sample.story.lower():
            print("MISMATCH: generated story lacks its happy ending.")
            return 1
    print("OK: ASP and Python agree on the happy ending.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a cautionary fable about an account with a happy ending."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--village", choices=VILLAGES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
        village=args.village or rng.choice(VILLAGES),
    )


def choose_arc(seed: int) -> FableArc:
    return ARCS[seed % len(ARCS)]


def tell(params: StoryParams) -> World:
    base = params.seed if params.seed is not None else sum(
        ord(ch) for ch in f"{params.name}|{params.trait}|{params.village}"
    )
    arc = choose_arc(base)
    world = World()

    hero = world.add(Entity(
        id="hero",
        type="child",
        label=params.name,
        memes={"curiosity": 1.0, "honesty": 0.0},
    ))
    account = world.add(Entity(
        id="account",
        type="account",
        label="the account book",
        owner="village",
        meters={"clear": 0.0, "risk": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        type="helper",
        label="the village keeper",
        owner="village",
    ))

    world.facts.update(
        hero=hero,
        account=account,
        helper=helper,
        arc=arc,
        opening=OPENINGS[(base // len(ARCS)) % len(OPENINGS)],
        request=DIALOGUE_REQUESTS[(base // 17) % len(DIALOGUE_REQUESTS)],
        reflection=REFLECTIONS[(base // 29) % len(REFLECTIONS)],
    )

    world.say(
        f"{world.facts['opening']} called {params.village}, "
        f"a {params.trait} child named {params.name} cared for the village account."
    )
    world.say(
        f"The account book held the record of seeds, eggs, lamps, and favors, "
        f"and {arc.temptation} appeared beside its careful columns."
    )

    world.para()
    world.say(
        f"The shortcut seemed easy: {arc.shortcut}. "
        f"{params.name} reached for the pen, but paused."
    )
    world.say(f'"{params.name}, {params.request}" the village keeper asked.')
    world.say(f'"{world.facts["request"]}" {params.name} replied.')
    world.say(
        f'The keeper pointed to the danger. "{arc.danger.capitalize()}."'
    )
    world.say(
        f"{params.name} looked again and chose to {arc.honest_action}."
    )

    hero.memes["honesty"] = 1.0
    account.meters["clear"] = 1.0
    account.meters["risk"] = 0.0
    world.fired.add("truth_told")

    world.para()
    world.say(arc.consequence)
    world.say(arc.repair)
    world.say(world.facts["reflection"])
    world.say(
        f"It was a happy ending because the account was made true before the "
        f"mistake could spread. {arc.final_image}"
    )
    world.say(f"The fable's lesson was simple: {arc.moral}")
    return world


def generation_prompts(world: World) -> list[str]:
    arc: FableArc = world.facts["arc"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a cautionary fable about {hero.label} and an account that tempts the child to {arc.shortcut}.",
        f"Tell a child-facing story with a happy ending in which {hero.label} learns that {arc.moral}",
        f"Write a fable where an account, a helper, an honest choice, and a repaired mistake lead to {arc.final_image}",
    ]


def story_qa(world: World) -> list[QAItem]:
    arc: FableArc = world.facts["arc"]
    hero: Entity = world.facts["hero"]
    return [
        QAItem(
            question="Who cared for the village account?",
            answer=f"{hero.label}, a {hero.type}, cared for the village account in {world.facts['opening'].lower().replace('in a small village ', '').replace('one clear morning in the village ', '').replace('at the edge of a green valley ', '').replace('when the market bell rang ', '')}.",
        ),
        QAItem(
            question=f"What temptation did {hero.label} find in the account?",
            answer=f"{hero.label} found {arc.temptation}. The tempting shortcut was {arc.shortcut}.",
        ),
        QAItem(
            question="What did the child do to prevent the account from becoming false?",
            answer=f"The child chose to {arc.honest_action}, so the account could be corrected before {arc.danger}.",
        ),
        QAItem(
            question="Why did the story have a happy ending?",
            answer=f"It had a happy ending because the truth was told, help was accepted, and {arc.repair[0].lower() + arc.repair[1:]}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an account?",
            answer="An account is a record that keeps track of things such as money, goods, promises, or actions.",
        ),
        QAItem(
            question="What makes a fable cautionary?",
            answer="A cautionary fable shows a tempting mistake and teaches how a wiser choice can prevent harm.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth and recording or describing things fairly, even when a mistake is embarrassing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Luna", trait="curious", village="Willowbrook", seed=11),
    StoryParams(name="Mira", trait="careful", village="Cloverfield", seed=22),
    StoryParams(name="Tavi", trait="kind", village="Mossy Hollow", seed=33),
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
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("happy ending:", any(atom.name == "happy_ending" for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
