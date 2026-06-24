#!/usr/bin/env python3
"""
A small mythic storyworld about a talkative child, a surprising find,
curiosity, and a shared gift that changes the day.
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


@dataclass
class Character:
    id: str
    name: str
    role: str
    talkative: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subj(self) -> str:
        return "they"

    def obj(self) -> str:
        return "them"

    def pos(self) -> str:
        return "their"


@dataclass
class Thing:
    id: str
    name: str
    kind: str
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    feature: str
    weather: str


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    gift: str
    seed: Optional[int] = None


SETTINGS = {
    "hill": Setting(place="the hill of old stones", feature="wind", weather="golden"),
    "shore": Setting(place="the shore of the moonlit sea", feature="waves", weather="silver"),
    "grove": Setting(place="the quiet grove", feature="moss", weather="green"),
}

HEROES = ["Mira", "Lio", "Naya", "Toma", "Iris", "Kian"]
COMPANIONS = ["bird", "fox", "rabbit", "cat", "goat", "wolf"]
GIFTS = {
    "bell": "a tiny bell",
    "pebble": "a warm pebble",
    "seed": "a shining seed",
    "shell": "a spiral shell",
    "ribbon": "a bright ribbon",
}


@dataclass
class World:
    setting: Setting
    entities: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]


def introduce(world: World, hero: Character) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there lived {hero.name}, "
        f"a talkative child who spoke to birds, stones, and the wind itself."
    )


def curiosity(world: World, hero: Character, gift: Thing) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.name} noticed {gift.name} half-hidden near the roots and felt a sharp, bright curiosity."
    )
    world.say(
        f"They leaned closer, asking the hush of the place what secret this small thing might keep."
    )


def surprise(world: World, hero: Character, gift: Thing) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    gift.memes["surprise"] = gift.memes.get("surprise", 0) + 1
    world.say(
        f"Then the object glimmered at once, and {hero.name} gave a startled laugh of surprise."
    )
    world.say(
        f"It was no ordinary treasure; it seemed made for a story older than the road beneath their feet."
    )


def sharing(world: World, hero: Character, companion: Character, gift: Thing) -> None:
    hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
    gift.shared_with.add(companion.id)
    world.say(
        f"{hero.name} did not keep the wonder alone."
    )
    world.say(
        f"They called to the {companion.role}, and together they shared {gift.name} as if sharing could wake the sky."
    )


def resolution(world: World, hero: Character, companion: Character, gift: Thing) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    companion.memes["joy"] = companion.memes.get("joy", 0) + 1
    world.say(
        f"After that, the two of them walked on laughing, and {world.setting.feature} seemed gentler than before."
    )
    world.say(
        f"{hero.name} kept talking, but now every word sounded like a blessing, and the day shone with shared good fortune."
    )


def tell(setting: Setting, hero_name: str, companion_role: str, gift_label: str) -> World:
    world = World(setting)
    hero = world.add(Character(id="hero", name=hero_name, role="child", talkative=True))
    companion = world.add(Character(id="companion", name=companion_role.capitalize(), role=companion_role))
    gift = world.add(Thing(id="gift", name=gift_label, kind="treasure", owner=None))

    introduce(world, hero)
    world.para()
    curiosity(world, hero, gift)
    surprise(world, hero, gift)
    world.para()
    sharing(world, hero, companion, gift)
    resolution(world, hero, companion, gift)

    world.facts.update(hero=hero, companion=companion, gift=gift, setting=setting)
    return world


def build_story(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero, params.companion, GIFTS[params.gift])
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
        f'Write a short myth for a child who is talkative, curious, and kind, set at {f["setting"].place}.',
        f"Tell a gentle story about {f['hero'].name} finding {f['gift'].name} and sharing it with a {f['companion'].role}.",
        "Write a mythic story where surprise leads to curiosity and ends in sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    companion: Character = f["companion"]
    gift: Thing = f["gift"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about in {setting.place}?",
            answer=f"It is about {hero.name}, a talkative child who loves to speak and wonder about the world.",
        ),
        QAItem(
            question=f"What made {hero.name} feel curious?",
            answer=f"{hero.name} became curious when they noticed {gift.name} hidden near the roots.",
        ),
        QAItem(
            question=f"What happened when the surprise was shared?",
            answer=f"{hero.name} shared {gift.name} with the {companion.role}, and both of them ended the day happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, listen, and learn what a thing really is.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else enjoy, use, or know about something too.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes a person pause and react with wonder.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, ent in world.entities.items():
        if isinstance(ent, Character):
            lines.append(f"{eid}: Character(name={ent.name}, role={ent.role}, memes={ent.memes})")
        else:
            lines.append(
                f"{eid}: Thing(name={ent.name}, kind={ent.kind}, owner={ent.owner}, shared_with={sorted(ent.shared_with)}, memes={ent.memes})"
            )
    return "\n".join(lines)


def explain_invalid(reason: str) -> None:
    raise StoryError(reason)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in HEROES:
            for companion in COMPANIONS:
                if hero.lower() != companion:
                    for gift in GIFTS:
                        combos.append((place, hero, companion, gift))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for h in HEROES:
        lines.append(asp.fact("hero", h.lower()))
    for c in COMPANIONS:
        lines.append(asp.fact("companion", c))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Hero, Comp, Gift) :- place(Place), hero(Hero), companion(Comp), gift(Gift), Hero != Comp.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    gift: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of talkative wonder and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--gift", choices=GIFTS)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HEROES)
    companion = args.companion or rng.choice(COMPANIONS)
    gift = args.gift or rng.choice(list(GIFTS))
    if hero.lower() == companion:
        raise StoryError("The hero and companion must be different beings.")
    return StoryParams(place=place, hero=hero, companion=companion, gift=gift)


CURATED = [
    StoryParams(place="hill", hero="Mira", companion="fox", gift="bell"),
    StoryParams(place="shore", hero="Lio", companion="bird", gift="shell"),
    StoryParams(place="grove", hero="Naya", companion="rabbit", gift="seed"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero, params.companion, GIFTS[params.gift])
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


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and python validity.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos")
        for c in combos[:50]:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} with {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
