#!/usr/bin/env python3
"""
A small storyworld about a sudden gush, a gentle transformation, and a happy
ending in nursery-rhyme style.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {"soaked": 0.0, "glow": 0.0, "mood": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hope": 0.0, "worry": 0.0, "joy": 0.0})
    form: str = "plain"
    transformed: bool = False

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Setting:
    place: str
    feature: str
    hush: str


@dataclass
class GushEvent:
    source: str
    intensity: str
    change: str
    sparkle: str


@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    gush: str
    seed: Optional[int] = None


SETTINGS: dict[str, Setting] = {
    "brook": Setting(place="the little brook", feature="brook", hush="softly"),
    "garden": Setting(place="the moonlit garden", feature="garden", hush="gently"),
    "fountain": Setting(place="the round fountain", feature="fountain", hush="brightly"),
}

HEROES = ["Mina", "Ned", "Lila", "Pip", "Bella", "Toby"]
FRIENDS = ["a snail", "a mouse", "a robin", "a lamb", "a kitten"]
GUSHES: dict[str, GushEvent] = {
    "water": GushEvent(source="a silver pipe", intensity="sudden", change="turned the plain sprite into a shining one", sparkle="sparkling"),
    "rain": GushEvent(source="a cloud above", intensity="sudden", change="turned the dusty kitten into a bright, clean kitty", sparkle="glistening"),
    "spray": GushEvent(source="the fountain rim", intensity="sudden", change="turned the shy little seed into a tall green sprout", sparkle="twinkling"),
}


@dataclass
class World:
    setting: Setting
    hero: Character
    friend: Character
    gush: GushEvent
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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"setting={self.setting.place!r} hush={self.setting.hush!r}")
        for who in (self.hero, self.friend):
            lines.append(
                f"{who.name}: form={who.form!r} transformed={who.transformed} "
                f"meters={{{', '.join(f'{k}: {v}' for k, v in who.meters.items() if v)}}} "
                f"memes={{{', '.join(f'{k}: {v}' for k, v in who.memes.items() if v)}}}"
            )
        lines.append(f"gush={self.gush.source!r} change={self.gush.change!r}")
        return "\n".join(lines)


def _meter(state: Character, key: str, delta: float) -> None:
    state.meters[key] = state.meters.get(key, 0.0) + delta


def _meme(state: Character, key: str, delta: float) -> None:
    state.memes[key] = state.memes.get(key, 0.0) + delta


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.gush not in GUSHES:
        raise StoryError("Unknown gush type.")
    if params.hero == params.friend:
        raise StoryError("The hero and the friend must be different.")


def ASP_RULES() -> str:
    return r"""
% A gush can begin a transformation when it reaches the hero.
gush_reaches_hero(G) :- gush(G), flows_to_hero(G).

% Transformation happens if the gush is strong enough and the hero is willing.
transforms(H, G) :- hero(H), gush_reaches_hero(G), willing(H).

% A happy ending follows when transformation happens and the friend stays close.
happy_ending(H, F) :- transforms(H, _), friend(F), nearby(F).
#show transforms/2.
#show happy_ending/2.
"""


def asp_facts(params: StoryParams) -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", params.setting),
        asp.fact("hero", "hero"),
        asp.fact("friend", "friend"),
        asp.fact("gush", params.gush),
        asp.fact("flows_to_hero", params.gush),
        asp.fact("willing", "hero"),
        asp.fact("nearby", "friend"),
    ]
    return "\n".join(lines)


def asp_program(params: StoryParams) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES()}\n"


def asp_models(params: StoryParams) -> list[list]:
    import storyworlds.asp as asp
    return asp.solve(asp_program(params), models=0)


def asp_verify(params: StoryParams) -> int:
    import storyworlds.asp as asp
    models = asp_models(params)
    atoms = [asp.atoms(m, "transforms") for m in models]
    expected = [(("hero", params.gush),)]
    if atoms and any(("hero", params.gush) in m for m in atoms):
        return 0
    return 1


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.setting]
    gush = GUSHES[params.gush]
    hero = Character(name=params.hero, kind="hero")
    friend = Character(name=params.friend, kind="friend")
    world = World(setting=setting, hero=hero, friend=friend, gush=gush)

    world.say(f"By {setting.place}, where the reeds bent low, little {hero.name} was quiet and small.")
    _meme(hero, "worry", 1)
    _meme(hero, "hope", 1)
    world.say(
        f"{hero.name} loved the {setting.feature}, and {friend.name} kept near, "
        f"toddling along {setting.hush}."
    )

    world.para()
    world.say(
        f"Then came a {gush.intensity} gush from {gush.source}, with a {gush.sparkle} splash and a merry swoosh."
    )
    _meter(hero, "soaked", 1)
    _meme(hero, "worry", 1)
    world.say(f"It splashed {hero.name} from head to toe, and {hero.name} gasped, but did not go." )
    world.say(f"{friend.name} blinked and stayed close, as small ripples stitched rings in a row.")

    world.para()
    world.say(
        f"The water did not only wet {hero.name}; it began to change what was inside and in view."
    )
    _meter(hero, "glow", 1)
    _meme(hero, "joy", 1)
    hero.form = "shining"
    hero.transformed = True
    world.say(
        f"With a soft little shimmer, {gush.change}, and {hero.name} became {gush.change.split(' into ')[-1]}."
    )
    world.say(
        f"{hero.name}'s face grew bright, {friend.name} clapped, and the whole pond seemed to sing."
    )

    world.para()
    _meme(hero, "joy", 1)
    world.say(
        f"Now {hero.name} laughed and played {setting.hush}, no longer plain, but gleaming and gay."
    )
    world.say(
        f"{friend.name} danced beside {hero.name}, and the moon over {setting.place} looked down with a silver bouquet."
    )
    world.say(
        f"So the gust became a blessing, the splash became a song, and the little night ended happy and strong."
    )

    world.facts.update(
        hero=hero.name,
        friend=friend.name,
        setting=params.setting,
        gush=params.gush,
        transformed=hero.transformed,
        happy_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story for a child about "{f["gush"]}" that brings a transformation and a happy ending.',
        f"Tell a gentle story about {f['hero']} and {f['friend']} at the {f['setting']} when a sudden gush changes what happens next.",
        "Write a small rhyming story where a splash leads from worry to wonder and ends in joy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who was changed by the gush in the story?",
            answer=f"{f['hero']} was changed by the gush, and the change made them shine and feel happy.",
        ),
        QAItem(
            question=f"What happened after the sudden gush arrived?",
            answer=f"After the sudden gush arrived, {f['hero']} became transformed and the story turned into a happy ending.",
        ),
        QAItem(
            question=f"Who stayed near {f['hero']} during the splash?",
            answer=f"{f['friend']} stayed near {f['hero']} during the splash and helped make the moment feel safe and warm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gush?",
            answer="A gush is a sudden rush of water or liquid that comes out quickly.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a change from one form or state into another.",
        ),
        QAItem(
            question="What makes a happy ending in a story?",
            answer="A happy ending is when the trouble is solved and the story closes with joy or safety.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about a gush and a transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--gush", choices=GUSHES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gush = args.gush or rng.choice(list(GUSHES))
    hero = args.hero or rng.choice(HEROES)
    friend = args.friend or rng.choice([f for f in FRIENDS if f != hero])
    if hero == friend:
        raise StoryError("Hero and friend must differ.")
    return StoryParams(setting=setting, hero=hero, friend=friend, gush=gush)


def generate(params: StoryParams) -> StorySample:
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="brook", hero="Mina", friend="a snail", gush="water"),
    StoryParams(setting="garden", hero="Pip", friend="a robin", gush="rain"),
    StoryParams(setting="fountain", hero="Lila", friend="a kitten", gush="spray"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(StoryParams(setting="brook", hero="Mina", friend="a snail", gush="water")))
        return

    if args.verify:
        params = StoryParams(setting="brook", hero="Mina", friend="a snail", gush="water")
        sys.exit(asp_verify(params))

    if args.asp:
        params = StoryParams(setting=args.setting or "brook", hero=args.hero or "Mina", friend=args.friend or "a snail", gush=args.gush or "water")
        import storyworlds.asp as asp
        models = asp_models(params)
        print(f"{len(models)} model(s)")
        for i, model in enumerate(models, 1):
            print(f"model {i}: {model}")
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(seed + i))
            p.seed = seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
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
            header = f"### {p.hero} / {p.gush} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
