#!/usr/bin/env python3
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

MORALS = {
    "sharing": "sharing made the meal sweeter for everyone",
    "honesty": "honesty kept the magic from twisting the day",
    "kindness": "kindness was the strongest spell of all",
}

FLAVORS = {
    "apple": ("apple flavor", "smelled like warm apples"),
    "berry": ("berry flavor", "tasted bright and sweet"),
    "honey": ("honey flavor", "tasted golden and rich"),
    "mint": ("mint flavor", "felt cool and fresh"),
}

MAGICS = {
    "spark": "a tiny spark of magic",
    "charm": "a glowing charm",
    "whisper": "a magic whisper",
}

PLACES = {
    "orchard": "the orchard",
    "kitchen": "the kitchen",
    "meadow": "the meadow",
    "lantern_hill": "Lantern Hill",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    place: str = "orchard"
    flavor: str = "apple"
    magic: str = "spark"
    moral: str = "sharing"
    hero_name: str = "Yankee"
    hero_type: str = "fox"
    helper_name: str = "Moss"
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", *()),
    ]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FLAVORS:
        lines.append(asp.fact("flavor", fid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    for moral in MORALS:
        lines.append(asp.fact("moral", moral))
    lines.append(asp.fact("can_share", "apple"))
    lines.append(asp.fact("can_share", "berry"))
    lines.append(asp.fact("can_share", "honey"))
    lines.append(asp.fact("can_share", "mint"))
    return "\n".join(lines)


ASP_RULES = r"""
shared_flavor(F) :- can_share(F).
good_story(P, F, M, G) :- place(P), shared_flavor(F), moral(M), magic(G).
#show good_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, f, m, g) for p in PLACES for f in FLAVORS for m in MORALS for g in MAGICS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/4."))
    return sorted(set(asp.atoms(model, "good_story")))


def _taste_sentence(flavor: str) -> str:
    return FLAVORS[flavor][1]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("That place does not exist in this little fable.")
    if params.flavor not in FLAVORS:
        raise StoryError("That flavor is not in the story's pantry.")
    if params.magic not in MAGICS:
        raise StoryError("That kind of magic is not in the story's spellbook.")
    if params.moral not in MORALS:
        raise StoryError("That moral is not part of this fable.")
    if params.hero_name.strip().lower() == "yankee" and params.hero_type != "fox":
        raise StoryError("In this world, Yankee is the fox hero.")
    if params.flavor == "mint" and params.place == "orchard":
        raise StoryError("Mint flavor does not fit the orchard's apple path well enough for this fable.")


def tell(params: StoryParams) -> World:
    w = World(place=PLACES[params.place])
    hero = w.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = w.add(Entity(id=params.helper_name, kind="character", type="mouse"))
    bowl = w.add(Entity(id="bowl", type="bowl", label=f"a bowl of {params.flavor} juice", owner=hero.id))
    charm = w.add(Entity(id="charm", type="magic", label=MAGICS[params.magic], owner=helper.id))
    hero.meters["hunger"] = 1
    hero.memes["desire"] = 1
    hero.memes["greed"] = 1
    w.say(f"Once in {w.place}, there lived a clever fox named {hero.id}.")
    w.say(f"{hero.id} loved {params.flavor} flavor because it {_taste_sentence(params.flavor)}.")
    w.say(f"One day, {helper.id} found {charm.label} beside {w.place}.")
    w.para()
    w.say(f"The charm glimmered over the bowl and made the smell seem even stronger.")
    w.say(f"{hero.id} wanted all the {params.flavor} taste for himself, so he pushed the bowl close.")
    hero.memes["greed"] += 1
    bowl.meters["fullness"] = 1
    if params.magic == "spark":
        bowl.memes["shine"] = 1
    w.say(f"But the magic did not like a selfish heart, and the bowl began to wobble.")
    w.para()
    if params.moral == "sharing":
        hero.memes["regret"] = 1
        hero.memes["greed"] = 0
        helper.memes["trust"] = 1
        w.say(f"{helper.id} said, '{hero.id}, a flavor is sweeter when it is shared.'")
        w.say(f"{hero.id} nodded, split the bowl in two, and gave {helper.id} a fair sip.")
        w.say(f"Then the charm shone softly, and both friends laughed as the {params.flavor} taste filled the evening.")
    elif params.moral == "honesty":
        hero.memes["regret"] = 1
        w.say(f"{hero.id} told the truth about wanting the whole bowl.")
        w.say(f"The charm warmed at the honest words, and {helper.id} poured out two little cups instead.")
        w.say(f"They drank together, and the magic stayed gentle and bright.")
    else:
        hero.memes["kindness"] = 1
        w.say(f"{helper.id} smiled and offered first taste to {hero.id}.")
        w.say(f"{hero.id} answered with a kind bow and shared the bowl back.")
        w.say(f"The charm glowed like a lantern, and the whole place felt peaceful.")
    w.say(f"In the end, {hero.id} learned that {MORALS[params.moral]}.")
    w.facts.update(hero=hero, helper=helper, bowl=bowl, charm=charm, params=params)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short fable for children set in {PLACES[p.place]} about a fox named {p.hero_name} and the flavor of {p.flavor}.',
        f"Tell a gentle magical fable where {p.hero_name} meets {p.helper_name}, finds {MAGICS[p.magic]}, and learns why {MORALS[p.moral]}.",
        f'Create a simple moral story that includes "yankee", "flavor", and a small magic moment in {PLACES[p.place]}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Who was the fox in the story?",
            answer=f"The fox was {hero.id}, a clever little {hero.type} who lived in {PLACES[p.place]}.",
        ),
        QAItem(
            question=f"What flavor did {hero.id} love?",
            answer=f"{hero.id} loved {p.flavor} flavor, which {_taste_sentence(p.flavor)}.",
        ),
        QAItem(
            question=f"What did {helper.id} bring into the story?",
            answer=f"{helper.id} brought {MAGICS[p.magic]}, and it made the bowl of {p.flavor} taste feel magical.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that {MORALS[p.moral]}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that uses talking characters to teach a moral.",
        ),
        QAItem(
            question="What is a moral in a story?",
            answer="A moral is the lesson the story wants you to remember after it ends.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something impossible or wonderful happens, like a charm shining or a spell working.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = []
    out.append("== Prompts ==")
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small magical fable world about Yankee and flavor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--flavor", choices=FLAVORS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--hero-name", default="Yankee")
    ap.add_argument("--hero-type", default="fox", choices=["fox", "boy", "girl"])
    ap.add_argument("--helper-name", default="Moss")
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
    params = StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        flavor=args.flavor or rng.choice(list(FLAVORS)),
        magic=args.magic or rng.choice(list(MAGICS)),
        moral=args.moral or rng.choice(list(MORALS)),
        hero_name=args.hero_name or "Yankee",
        hero_type=args.hero_type or "fox",
        helper_name=args.helper_name or rng.choice(["Moss", "Pip", "Fern"]),
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show good_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/4."))
        combos = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="orchard", flavor="apple", magic="spark", moral="sharing"),
            StoryParams(place="meadow", flavor="berry", magic="charm", moral="kindness"),
            StoryParams(place="kitchen", flavor="honey", magic="whisper", moral="honesty"),
        ]
        samples = [generate(p) for p in curated]
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

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
