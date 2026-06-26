#!/usr/bin/env python3
"""
A small pirate-tale story world about an archaeologic souvenir, a mistletoe
twist, and a misunderstanding that is resolved with a moral value choice.

The world is built around a child-friendly premise:
a pirate crew finds a curious souvenir during an archaeologic dig, but a
misunderstanding about a mistletoe sprig leads to a twist. The ending proves
what changed: the crew chooses kindness over pride and shares the prize fairly.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

SETTING_NAME = "the moonlit cove"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class CrewRole:
    title: str
    type: str
    trait: str
    line: str


@dataclass
class Relic:
    label: str
    phrase: str
    theme: str
    value: str
    is_souvenir: bool = True


@dataclass
class Token:
    label: str
    phrase: str
    effect: str
    symbol: str


@dataclass
class StoryParams:
    role: str
    relic: str
    token: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ROLES = {
    "captain": CrewRole("captain", "boy", "bold", "He loved leading the crew over the salty deck."),
    "navigator": CrewRole("navigator", "girl", "clever", "She loved reading the stars and old maps."),
    "deckhand": CrewRole("deckhand", "boy", "cheerful", "He loved helping with ropes and shiny finds."),
    "lookout": CrewRole("lookout", "girl", "quick", "She loved spotting things before anyone else."),
}

RELICS = {
    "amulet": Relic("amulet", "an old silver amulet", "archeologic", "a bright souvenir"),
    "coin": Relic("coin", "a carved gold coin", "archeologic", "a tiny souvenir"),
    "cup": Relic("cup", "a small clay cup", "archeologic", "a treasured souvenir"),
}

TOKENS = {
    "mistletoe": Token("mistletoe", "a green sprig of mistletoe", "a kindness sign", "mistletoe"),
    "twist": Token("twist", "a twist of rope", "a sudden turn", "twist"),
    "moral_value": Token("moral_value", "a moral value lesson", "a kinder choice", "moral value"),
    "misunderstanding": Token("misunderstanding", "a misunderstanding", "a mixed-up guess", "misunderstanding"),
}

GREETINGS = [
    "The sea was quiet, but the deck had a secret to tell.",
    "The lanterns rocked softly while the crew searched for treasure.",
    "Salt wind curled around the ship like a whisper from the deep.",
]

MORALS = [
    "kindness matters more than showing off",
    "sharing can turn a mistake into a happy ending",
    "a gentle word can untie a hard knot",
]


ASP_RULES = r"""
role(captain). role(navigator). role(deckhand). role(lookout).
relic(amulet). relic(coin). relic(cup).
token(mistletoe). token(twist). token(moral_value). token(misunderstanding).

compatible(R,T) :- relic(R), token(T).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROLES:
        lines.append(asp.fact("role", r))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for t in TOKENS:
        lines.append(asp.fact("token", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set((r, t) for r in RELICS for t in TOKENS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python compatibility ({len(clingo_set)} pairs).")
        return 0
    print("MISMATCH between clingo and Python compatibility")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: archeologic souvenir, mistletoe, twist.")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--name")
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
    role = args.role or rng.choice(list(ROLES))
    relic = args.relic or rng.choice(list(RELICS))
    token = args.token or rng.choice(list(TOKENS))
    return StoryParams(
        role=role,
        relic=relic,
        token=token,
        name=args.name or rng.choice(["Mira", "Finn", "Nell", "Jory", "Sailor"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    role = ROLES[params.role]
    relic = RELICS[params.relic]
    token = TOKENS[params.token]

    hero = world.add(Entity(id=params.name, kind="character", type="boy" if "He " in role.line else "girl", label=params.name))
    if params.role == "captain" or params.role == "deckhand":
        hero.type = "boy"
    else:
        hero.type = "girl"

    world.facts.update(hero=hero, role=role, relic=relic, token=token)
    world.say(random.choice(GREETINGS))
    world.say(
        f"{hero.id} was the {params.role} of the little ship, and {hero.pronoun()} loved the job because "
        f"{role.line.lower()}"
    )
    world.say(
        f"One day, the crew found {relic.phrase} during an archeologic dig near the cove. "
        f"It looked like a perfect souvenir, so everyone leaned in to admire it."
    )
    world.para()
    world.say(
        f"Then came the twist: someone hung {token.phrase} above the hatch, and a misunderstanding spread fast. "
        f"The crew thought the sprig meant they should fight over the relic, but it was only a sign for sharing."
    )
    world.say(
        f"{hero.id} felt the old pride tug hard, yet the moral value lesson was louder. "
        f"{hero.id} took a breath, smiled, and offered the souvenir to the whole crew."
    )
    world.para()
    world.say(
        f"That changed everything. The misunderstanding faded, the twist turned sweet, and the crew passed the "
        f"{relic.label} from hand to hand while the mistletoe swayed above them."
    )
    world.say(
        f"In the end, the little ship sailed on with a happier heart, and everyone remembered that {random.choice(MORALS)}."
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
    f = world.facts
    return [
        'Write a short pirate tale for a young child that includes archeologic, souvenir, and mistletoe.',
        f"Tell a story where {f['hero'].id} finds {f['relic'].phrase} and a misunderstanding about {f['token'].phrase} leads to a twist.",
        "Write a child-friendly pirate story that ends with kindness and sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    relic: Relic = f["relic"]
    token: Token = f["token"]
    role: CrewRole = f["role"]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {hero.id}, who served as the {list(ROLES).index(role.title) if False else role.title} of the little ship.",
        ),
        QAItem(
            question=f"What did the crew find during the dig?",
            answer=f"They found {relic.phrase}, which became a special souvenir.",
        ),
        QAItem(
            question=f"What caused the misunderstanding on the ship?",
            answer=f"The crew saw {token.phrase} and misunderstood it, thinking it meant they should argue instead of share.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the strange sign did not mean trouble at all; it was really a reminder to be kind and share.",
        ),
        QAItem(
            question="What moral value did the hero choose at the end?",
            answer="The hero chose kindness and sharing instead of pride.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an archeologic dig?",
            answer="An archeologic dig is a careful search for old things hidden in the ground.",
        ),
        QAItem(
            question="What is a souvenir?",
            answer="A souvenir is a keepsake that helps you remember a place or a special day.",
        ),
        QAItem(
            question="What is mistletoe?",
            answer="Mistletoe is a green plant with small white berries that people often hang up as a holiday sign.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    StoryParams(role="captain", relic="amulet", token="mistletoe", name="Finn"),
    StoryParams(role="navigator", relic="coin", token="twist", name="Mira"),
    StoryParams(role="lookout", relic="cup", token="misunderstanding", name="Nell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        pairs = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(pairs)} compatible relic/token pairs:")
        for r, t in pairs:
            print(f"  {r:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.role}, {p.relic}, {p.token}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
