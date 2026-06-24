#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a shy speaker, a flower's ovary, and a
beauty ribbon that must be shared before the friends can reconcile.

Seed tale idea:
- A little child visits a garden rhyme-circle.
- A rabbit stutters while reading a rhyme about a flower ovary.
- A sparrow and a bee both want the beauty ribbon.
- The friends quarrel, then share the ribbon and calm down.
- The ending proves the turn: they sing together, and the garden feels bright.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "queen", "woman", "bee"}
        masculine = {"boy", "father", "king", "man", "rabbit", "sparrow"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    place: str
    hero: str
    friend1: str
    friend2: str
    seed: Optional[int] = None


PLACES = {
    "garden": "the garden",
    "nursery": "the nursery",
    "meadow": "the meadow",
    "greenhouse": "the greenhouse",
}

HEROES = [
    ("Robin", "rabbit"),
    ("Mimi", "mouse"),
    ("Lola", "girl"),
    ("Ned", "boy"),
]

FRIENDS = [
    ("Pip", "sparrow"),
    ("Bea", "bee"),
    ("Dora", "duck"),
    ("Tilly", "turtle"),
]


def _m(world: World, eid: str, key: str) -> float:
    return world.entities[eid].meters.get(key, 0.0)


def _e(world: World, eid: str, key: str) -> float:
    return world.entities[eid].memes.get(key, 0.0)


def _addm(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _adde(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def tell(place: str, hero_name: str, hero_type: str, friend1_name: str, friend1_type: str,
         friend2_name: str, friend2_type: str) -> World:
    world = World(place=place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    f1 = world.add(Entity(id=friend1_name, kind="character", type=friend1_type))
    f2 = world.add(Entity(id=friend2_name, kind="character", type=friend2_type))
    flower = world.add(Entity(id="flower", type="flower", label="little flower"))
    ovary = world.add(Entity(id="ovary", type="ovary", label="flower ovary", owner="flower"))
    ribbon = world.add(Entity(id="ribbon", type="ribbon", label="beauty ribbon", plural=False))
    world.facts.update(hero=hero, f1=f1, f2=f2, flower=flower, ovary=ovary, ribbon=ribbon)

    world.say(f"Once in {place}, {hero_name} skipped softly to a little rhyme-ring under the sky.")
    world.say(
        f"{hero.pronoun().capitalize()} met {friend1_name} and {friend2_name}, and together they sang a tiny song "
        f"about a flower's ovary and the quiet beauty hiding inside a bud."
    )
    _adde(hero, "curiosity", 1)
    _adde(f1, "pride", 1)
    _adde(f2, "pride", 1)

    world.para()
    world.say(
        f"Then {friend1_name} found the beauty ribbon and lifted {ribbon.it()} high. "
        f"{friend2_name} wanted {ribbon.it()} too, and the two began to tug."
    )
    _adde(f1, "want", 1)
    _adde(f2, "want", 1)
    _adde(f1, "conflict", 1)
    _adde(f2, "conflict", 1)
    _addm(ribbon, "pulled", 1)
    world.say(
        f"The ribbon quivered like a bright thread of moonlight, and the little garden felt tense."
    )

    world.para()
    world.say(
        f"{hero_name} noticed the fuss and whispered a stuttering rhyme, "
        f'“B-b-beauty is b-best when it is shared.”'
    )
    _adde(hero, "care", 1)
    _adde(hero, "stutter", 1)
    _adde(f1, "listening", 1)
    _adde(f2, "listening", 1)

    if _e(world, "ribbon", "pulled") >= THRESHOLD:
        world.say(
            f"{hero_name} placed {hero.pronoun('possessive')} paws, hands, or wings gently between them "
            f"and suggested they hold {ribbon.it()} together."
        )
        _adde(f1, "sharing", 1)
        _adde(f2, "sharing", 1)
        _adde(f1, "reconciliation", 1)
        _adde(f2, "reconciliation", 1)
        f1.memes["conflict"] = 0.0
        f2.memes["conflict"] = 0.0
        ribbon.owner = "both"
        world.say(
            f"So {friend1_name} and {friend2_name} each held one end. They shared the ribbon, smiled, "
            f"and their grumpy faces turned round and mild."
        )

    world.para()
    world.say(
        f"After that, the friends sang together about the flower ovary, the bright ribbon, and the beauty of taking turns."
    )
    world.say(
        f"The garden grew calm again, and {hero_name} left with a happy little stutter-song and three friends in step."
    )

    world.facts["resolved"] = True
    return world


KNOWN_TOPICS = {
    "stutter": [
        QAItem(
            question="What is a stutter?",
            answer="A stutter is a way of speaking where a sound or word may repeat, as if the speaker is trying gently to find the next word.",
        )
    ],
    "ovary": [
        QAItem(
            question="What is a flower ovary?",
            answer="A flower ovary is a small part of a flower that helps make seeds after the flower is pollinated.",
        )
    ],
    "beauty": [
        QAItem(
            question="What does beauty mean?",
            answer="Beauty means something looks, sounds, or feels lovely and pleasing in a gentle way.",
        )
    ],
    "sharing": [
        QAItem(
            question="Why is sharing kind?",
            answer="Sharing is kind because more than one friend gets a turn, and everyone can feel included.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who had a disagreement make peace again and feel friendly once more.",
        )
    ],
}


ASP_RULES = r"""
% A ribbon is at risk of conflict when two friends want it at the same time.
want(X,ribbon) :- wants(X,ribbon).
want(Y,ribbon) :- wants(Y,ribbon).

conflict(ribbon) :- want(A,ribbon), want(B,ribbon), A != B.

sharing(ribbon) :- conflict(ribbon), offer_share(hero,ribbon).
reconciliation(ribbon) :- sharing(ribbon).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("wants", "friend1", "ribbon"))
    lines.append(asp.fact("wants", "friend2", "ribbon"))
    lines.append(asp.fact("offer_share", "hero", "ribbon"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld of conflict, sharing, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--friend1")
    ap.add_argument("--friend2")
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
    place = args.place or rng.choice(list(PLACES))
    hero_name, hero_type = rng.choice(HEROES)
    if args.name:
        hero_name = args.name
    f1_name, f1_type = rng.choice(FRIENDS)
    f2_name, f2_type = rng.choice(FRIENDS)
    if args.friend1:
        f1_name = args.friend1
    if args.friend2:
        f2_name = args.friend2
    return StoryParams(place=place, hero=hero_name, friend1=f1_name, friend2=f2_name)


def generate(params: StoryParams) -> StorySample:
    hero_type = next((t for n, t in HEROES if n == params.hero), "rabbit")
    f1_type = next((t for n, t in FRIENDS if n == params.friend1), "sparrow")
    f2_type = next((t for n, t in FRIENDS if n == params.friend2), "bee")
    world = tell(PLACES[params.place], params.hero, hero_type, params.friend1, f1_type, params.friend2, f2_type)
    story = world.render()
    prompts = [
        "Write a tiny nursery rhyme about a shy speaker who learns to share a beauty ribbon.",
        "Tell a gentle garden story that includes the words stutter, ovary, and beauty.",
        "Write a short tale where a small conflict ends in sharing and reconciliation.",
    ]
    hero = world.facts["hero"]
    f1 = world.facts["f1"]
    f2 = world.facts["f2"]
    ribbon = world.facts["ribbon"]
    story_qa = [
        QAItem(
            question=f"Who stuttered in the garden story?",
            answer=f"{hero.id} did. {hero.id} spoke with a little stutter when {hero.id} asked the friends to share.",
        ),
        QAItem(
            question="What did the friends quarrel over?",
            answer=f"They quarrelled over the beauty ribbon, because both {f1.id} and {f2.id} wanted it at once.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with sharing and reconciliation, and the friends sang together again in peace.",
        ),
    ]
    world_qa = []
    for key in ("stutter", "ovary", "beauty", "sharing", "reconciliation"):
        world_qa.extend(KNOWN_TOPICS[key])
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, h[0], f1[0]) for p in PLACES for h in HEROES for f1 in FRIENDS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show sharing/1.\n#show reconciliation/1."))
    return sorted(set(asp.atoms(model, "conflict")) | set(asp.atoms(model, "sharing")) | set(asp.atoms(model, "reconciliation")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show sharing/1.\n#show reconciliation/1."))
    got = set(asp.atoms(model, "reconciliation"))
    if got:
        print("OK: ASP rules produce reconciliation.")
        return 0
    print("MISMATCH: ASP rules did not produce reconciliation.")
    return 1


CURATED = [
    StoryParams(place="garden", hero="Robin", friend1="Pip", friend2="Bea"),
    StoryParams(place="nursery", hero="Mimi", friend1="Dora", friend2="Tilly"),
    StoryParams(place="meadow", hero="Lola", friend1="Pip", friend2="Bea"),
    StoryParams(place="greenhouse", hero="Ned", friend1="Dora", friend2="Tilly"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show conflict/1.\n#show sharing/1.\n#show reconciliation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin available; this storyworld uses a simple deterministic conflict -> sharing -> reconciliation pattern.")
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
