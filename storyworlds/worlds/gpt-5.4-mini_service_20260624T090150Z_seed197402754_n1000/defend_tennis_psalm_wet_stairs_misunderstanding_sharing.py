#!/usr/bin/env python3
"""
Storyworld: defend / tennis / psalm
A small slice-of-life simulation set on wet stairs, built around a misunderstanding
that is resolved through sharing.
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
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
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
class World:
    place: str
    weather: str = "drizzly"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    name: str
    sibling: str
    instrument: str
    seed: Optional[int] = None


ACTIVITY = {
    "tennis": {
        "verb": "play tennis",
        "gerund": "playing tennis",
        "rush": "run down the stairs with the racket",
        "sound": "The soft thump of a tennis ball felt cheerful, even indoors.",
    }
}

SETTING = "the wet stairs"

PRAYER = "psalm"

SIBLINGS = [
    ("Maya", "boy", "brother", "father"),
    ("Nina", "girl", "sister", "mother"),
    ("Leo", "boy", "brother", "mother"),
    ("Iris", "girl", "sister", "father"),
]

TRAITS = ["quiet", "curious", "gentle", "careful", "lively"]


@dataclass
class ActorPack:
    hero: Entity
    sibling: Entity
    ball: Entity
    racket: Entity
    hymnbook: Entity
    mat: Entity


def introduce(world: World, hero: Entity, sibling: Entity) -> None:
    world.say(
        f"{hero.id} was a {random.choice(TRAITS)} child who liked small after-school games."
    )
    world.say(
        f"{sibling.id} was {hero.pronoun('possessive')} {sibling.label}, and the two of them "
        f"often shared whatever they could fit on one stair."
    )


def setup(world: World, pack: ActorPack) -> None:
    hero, sibling = pack.hero, pack.sibling
    world.say(
        f"One rainy afternoon, {hero.id} and {sibling.id} sat on {SETTING} with a ball, a racket, and a songbook."
    )
    world.say(
        f"{hero.id} wanted to {ACTIVITY['tennis']['verb']}, while {sibling.id} was trying to read a psalm softly."
    )
    world.say(ACTIVITY["tennis"]["sound"])
    world.facts["shared_place"] = SETTING


def misunderstanding(world: World, pack: ActorPack) -> None:
    hero, sibling = pack.hero, pack.sibling
    hero.memes["want_game"] = hero.memes.get("want_game", 0) + 1
    sibling.memes["want_quiet"] = sibling.memes.get("want_quiet", 0) + 1
    hero.memes["frustration"] = hero.memes.get("frustration", 0) + 1
    sibling.memes["misunderstanding"] = sibling.memes.get("misunderstanding", 0) + 1
    world.say(
        f"{sibling.id} frowned and thought {hero.id} was being careless with the racket."
    )
    world.say(
        f"{hero.id} thought {sibling.id} was defending the stairs from play, not just trying to keep the psalm quiet."
    )
    world.facts["misunderstanding"] = True


def defend_stairs(world: World, pack: ActorPack) -> None:
    hero, sibling, mat = pack.hero, pack.sibling, pack.mat
    hero.meters["careful_steps"] = hero.meters.get("careful_steps", 0) + 1
    mat.meters["dry_spot"] = mat.meters.get("dry_spot", 0) + 1
    world.say(
        f"Then {hero.id} noticed the steps were wet and slippery, so {hero.id} spread a little mat over the safest step."
    )
    world.say(
        f"{hero.id} said, \"I wasn't trying to make trouble. I was trying to defend our feet from slipping.\""
    )
    world.facts["defend"] = True


def sharing(world: World, pack: ActorPack) -> None:
    hero, sibling, ball, racket, hymnbook = pack.hero, pack.sibling, pack.ball, pack.racket, pack.hymnbook
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    sibling.memes["kindness"] = sibling.memes.get("kindness", 0) + 1
    hero.memes["frustration"] = 0
    sibling.memes["misunderstanding"] = 0
    ball.worn_by = hero.id
    racket.worn_by = hero.id
    hymnbook.worn_by = sibling.id
    world.say(
        f"{sibling.id} looked again and smiled, because {hero.id} had meant to share the space, not interrupt the prayer."
    )
    world.say(
        f"So they made a tiny plan: {sibling.id} kept reading the psalm on the dry side, and {hero.id} bounced the tennis ball quietly on the mat."
    )
    world.say(
        f"After that, they shared the stairs the way neighbors share a porch, with room for both a game and a song."
    )
    world.facts["sharing"] = True


def ending(world: World, pack: ActorPack) -> None:
    hero, sibling = pack.hero, pack.sibling
    world.say(
        f"By the end, the wet stairs were still wet, but nobody was upset anymore."
    )
    world.say(
        f"{hero.id} had a safe place to {ACTIVITY['tennis']['verb']}, {sibling.id} had a calm place to read the psalm, and the two of them walked away side by side."
    )


def build_world(params: StoryParams) -> World:
    hero_name = params.name
    sibling_name, sibling_type, sibling_label, parent_type = next(
        (n, t, l, p) for (n, t, l, p) in SIBLINGS if n != params.name
    ) if params.name in {n for n, *_ in SIBLINGS} else random.choice(SIBLINGS)

    world = World(place=SETTING)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label="child"))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_type, label=sibling_label))
    ball = world.add(Entity(id="ball", label="tennis ball", type="ball", plural=False, owner=hero.id))
    racket = world.add(Entity(id="racket", label="tennis racket", type="racket", owner=hero.id))
    hymnbook = world.add(Entity(id="hymnbook", label="psalm book", type="book", owner=sibling.id))
    mat = world.add(Entity(id="mat", label="small mat", type="mat", owner=hero.id))
    world.facts.update(
        hero=hero,
        sibling=sibling,
        ball=ball,
        racket=racket,
        hymnbook=hymnbook,
        mat=mat,
        parent_type=parent_type,
        instrument=params.instrument,
    )

    introduce(world, hero, sibling)
    world.para()
    setup(world, ActorPack(hero, sibling, ball, racket, hymnbook, mat))
    misunderstanding(world, ActorPack(hero, sibling, ball, racket, hymnbook, mat))
    world.para()
    defend_stairs(world, ActorPack(hero, sibling, ball, racket, hymnbook, mat))
    sharing(world, ActorPack(hero, sibling, ball, racket, hymnbook, mat))
    ending(world, ActorPack(hero, sibling, ball, racket, hymnbook, mat))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    return [
        f'Write a short slice-of-life story about {hero.id}, tennis, and a psalm on wet stairs.',
        f"Tell a gentle story where {hero.id} and {sibling.id} misunderstand each other, then share the stairs.",
        f'Write a child-friendly story that includes the words "defend", "tennis", and "psalm".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {sibling.id} spend time in the story?",
            answer=f"They spent time on {SETTING}. The stairs were wet, so they had to be careful about slipping.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do while {sibling.id} read?",
            answer=f"{hero.id} wanted to play tennis while {sibling.id} read a psalm softly.",
        ),
        QAItem(
            question=f"Why was there a misunderstanding between them?",
            answer=(
                f"{sibling.id} first thought {hero.id} was being careless, and {hero.id} thought {sibling.id} was trying to stop the game. "
                f"They were really just trying to use the same small space in different ways."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} defend the stairs?",
            answer=(
                f"{hero.id} put a small mat on a safer step and explained that the idea was to defend everyone's feet from slipping on the wet stairs."
            ),
        ),
        QAItem(
            question=f"How did they solve the problem at the end?",
            answer=(
                f"They shared the stairs. {sibling.id} kept reading the psalm on one side, and {hero.id} played tennis quietly on the mat on the other side."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tennis?",
            answer="Tennis is a game where people hit a ball with rackets and try to keep it in play.",
        ),
        QAItem(
            question="What is a psalm?",
            answer="A psalm is a song or prayer that people can read or sing quietly.",
        ),
        QAItem(
            question="Why are wet stairs dangerous?",
            answer="Wet stairs can be slippery, so people need to walk carefully to avoid falling.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use something or enjoy a space together.",
        ),
        QAItem(
            question="What does defend mean in a story like this?",
            answer="To defend something means to protect it or keep it safe from harm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        parts.append(f"{e.id}: {e.type} {' '.join(bits)}")
    parts.append(f"facts={world.facts}")
    return "\n".join(parts)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "wet_stairs"),
            asp.fact("activity", "tennis"),
            asp.fact("virtue", "defend"),
            asp.fact("virtue", "sharing"),
            asp.fact("text", "psalm"),
            asp.fact("place_feature", "wet"),
            asp.fact("place_feature", "stairs"),
        ]
    )


ASP_RULES = r"""
setting(wet_stairs).
activity(tennis).
theme(defend).
theme(sharing).
keyword(psalm).

child_story(S) :- setting(S), activity(tennis), theme(defend), theme(sharing), keyword(psalm).

#show child_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: defend, tennis, psalm on wet stairs.")
    ap.add_argument("--name", choices=["Maya", "Nina", "Leo", "Iris"], default="Maya")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(["Maya", "Nina", "Leo", "Iris"]),
        sibling=rng.choice(["brother", "sister", "friend"]),
        instrument=PRAYER,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show child_story/1."))
    atoms = asp.atoms(model, "child_story")
    if atoms == [("wet_stairs",)]:
        print("OK: ASP twin matches the Python story gate.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected child_story/1 fact.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show child_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show child_story/1."))
        print(asp.atoms(model, "child_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(name=name, sibling="friend", instrument=PRAYER, seed=base_seed)) for name in ["Maya", "Nina", "Leo", "Iris"]]
    else:
        for i in range(max(args.n, 1)):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
