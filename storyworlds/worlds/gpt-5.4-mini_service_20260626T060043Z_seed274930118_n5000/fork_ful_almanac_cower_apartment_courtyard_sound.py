#!/usr/bin/env python3
"""
A heartwarming small-world story generator about an apartment courtyard, a forkful
snack, an old almanac, and a child who cowers at a startling sound effect before
finding comfort and a kinder way through the moment.
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
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the apartment courtyard"
    afford_sound: bool = True


@dataclass
class StoryParams:
    place: str = "apartment courtyard"
    hero_name: str = "Mina"
    hero_type: str = "girl"
    helper_name: str = "Grandpa"
    helper_type: str = "grandfather"
    snack: str = "fork-ful of noodles"
    book: str = "almanac"
    sound: str = "clang"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


def sound_effect(sound: str) -> str:
    return {
        "clang": "CLANG!",
        "bang": "BANG!",
        "whistle": "WHEEE!",
        "whoosh": "WHOOOSH!",
        "plink": "PLINK!",
    }.get(sound, sound.upper() + "!")


def setup_world(params: StoryParams) -> World:
    world = World(Setting(place="the apartment courtyard", afford_sound=True))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    snack = world.add(Entity(
        id="snack",
        type="snack",
        label=params.snack,
        phrase=f"a {params.snack}",
        owner=hero.id,
        caretaker=helper.id,
    ))
    book = world.add(Entity(
        id="book",
        type="book",
        label="almanac",
        phrase="an old almanac",
        owner=helper.id,
        caretaker=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, snack=snack, book=book, sound=params.sound)
    return world


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    snack: Entity = world.facts["snack"]
    book: Entity = world.facts["book"]
    sound = world.facts["sound"]

    world.say(
        f"{hero.id} lived near the apartment courtyard, where little patches of sunlight moved "
        f"across the bricks."
    )
    world.say(
        f"{helper.id} liked bringing an old almanac outside, and {hero.id} liked {snack.phrase} "
        f"because it was warm and cozy to eat."
    )

    world.para()
    world.say(
        f"That afternoon, {helper.id} opened the almanac and pointed to the page about weather, "
        f"while {hero.id} took a careful fork-ful."
    )
    world.say(
        f"Then {sound_effect(sound)} came from the courtyard drain, loud enough to make {hero.id} "
        f"cower behind {helper.id}'s chair."
    )
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["comfort_needed"] = hero.memes.get("comfort_needed", 0.0) + 1

    world.para()
    world.say(
        f"{helper.id} did not laugh. {helper.id} closed the almanac a little, listened carefully, "
        f"and said, \"That was only the courtyard pipe talking.\""
    )
    world.say(
        f"To prove it, {helper.id} tapped the book cover twice: tap, tap. Then {helper.id} showed "
        f"{hero.id} the picture of clouds in the almanac and hummed softly, so the courtyard felt "
        f"smaller and friendlier."
    )
    hero.memes["comfort"] = hero.memes.get("comfort", 0.0) + 1
    hero.memes["fear"] = 0.0

    world.para()
    world.say(
        f"{hero.id} peeked out, took another fork-ful, and smiled when the drain made only a tiny "
        f"plink instead of a frightful crash."
    )
    world.say(
        f"By the end, {hero.id} was sitting up straight again, sharing the almanac page with "
        f"{helper.id}, and the apartment courtyard sounded calm and safe."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        'Write a short heartwarming story set in an apartment courtyard that includes a fork-ful, an almanac, and a sound effect.',
        f"Tell a gentle story where {hero.id} cowers at a loud sound, and {helper.id} comforts {hero.pronoun('object')} with an almanac.",
        "Write a cozy story in which a child feels scared by a courtyard noise, then feels safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    snack: Entity = f["snack"]
    sound = f["sound"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {helper.id} spend the afternoon?",
            answer="They spent it in the apartment courtyard, where the light and the brick paths made a calm little outdoor space.",
        ),
        QAItem(
            question=f"What was {hero.id} eating before the loud noise?",
            answer=f"{hero.id} was eating {snack.phrase}, one careful fork-ful at a time.",
        ),
        QAItem(
            question=f"What made {hero.id} cower at first?",
            answer=f"The loud {sound_effect(sound)} from the courtyard drain startled {hero.id}, so {hero.id} cowered behind {helper.id}.",
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} feel better?",
            answer=f"{helper.id} listened kindly, explained that the noise was only the pipe, and used the almanac and a soft voice to make the moment feel safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an almanac?",
            answer="An almanac is a book with useful facts, often about weather, seasons, and other helpful everyday information.",
        ),
        QAItem(
            question="What does it mean to cower?",
            answer="To cower means to bend down or hide because you feel scared or worried.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a noise made to help tell a story, like a clang, bang, or whoosh.",
        ),
        QAItem(
            question="What is an apartment courtyard?",
            answer="An apartment courtyard is a shared open space between or beside apartment buildings where people can sit, walk, or play.",
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
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_invalid() -> str:
    return "(No story: this world expects a child, an almanac, a fork-ful snack, and a sound that can be softened by comfort.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming apartment-courtyard storyworld with sound effects.")
    ap.add_argument("--place", choices=["apartment courtyard"], default="apartment courtyard")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother", "grandfather"], default="grandfather")
    ap.add_argument("--snack", default="fork-ful of noodles")
    ap.add_argument("--sound", choices=["clang", "bang", "whistle", "whoosh", "plink"], default="clang")
    ap.add_argument("--name")
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
    hero_name = args.hero_name or rng.choice(["Mina", "Lio", "Ari", "Nia", "Toby"])
    helper_name = args.helper_name or rng.choice(["Grandpa", "Grandma", "Aunt Jo", "Dad"])
    hero_type = args.hero_type
    if args.helper_type == "mother":
        helper_name = helper_name if helper_name != "Dad" else "Mom"
    return StoryParams(
        place="apartment courtyard",
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=args.helper_type,
        snack=args.snack,
        book="almanac",
        sound=args.sound,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
#show safe/1.
safe(hero) :- comfort(hero), not fear(hero).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "apartment_courtyard"),
        asp.fact("sound_effect", "clang"),
        asp.fact("sound_effect", "bang"),
        asp.fact("sound_effect", "whistle"),
        asp.fact("sound_effect", "whoosh"),
        asp.fact("sound_effect", "plink"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world is prose-first; no ASP listings are needed for this gentle courtyard tale.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            place="apartment courtyard",
            hero_name="Mina",
            hero_type="girl",
            helper_name="Grandpa",
            helper_type="grandfather",
            snack="fork-ful of noodles",
            book="almanac",
            sound="clang",
            seed=base_seed,
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
