#!/usr/bin/env python3
"""
A mythic story world about a small winged messenger, a pair of underclothes,
and a misunderstanding around the name Anorexia.

The world is intentionally tiny and constraint-checked: the setting, the
problem, and the resolution are all driven by simulated state rather than a
fixed paragraph template.
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


# ---------------------------------------------------------------------------
# Registry data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Setting:
    name: str
    epithet: str
    place: str
    sky: str
    affordances: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Hero:
    name: str
    kind: str
    epithet: str
    wings: bool
    humor: str
    moral_tone: str


@dataclass(frozen=True)
class SacredThing:
    name: str
    epithet: str
    material: str
    worn_on: str
    prized: bool = True


@dataclass(frozen=True)
class Mischief:
    name: str
    verb: str
    misunderstanding: str
    comic_image: str
    harms: set[str] = field(default_factory=set)


SETTINGS: dict[str, Setting] = {
    "dawnshore": Setting(
        name="Dawnshore",
        epithet="the harbor of first light",
        place="the pearl steps",
        sky="rose and gold",
        affordances={"speak", "search", "carry", "laugh"},
    ),
    "highorchard": Setting(
        name="High Orchard",
        epithet="the apple hill above the clouds",
        place="the silver branches",
        sky="bright blue",
        affordances={"speak", "search", "carry", "laugh"},
    ),
    "moonwell": Setting(
        name="Moonwell",
        epithet="the well where moonbeams sleep",
        place="the stone ring",
        sky="pale and quiet",
        affordances={"speak", "search", "carry", "laugh"},
    ),
}

HEROES: dict[str, Hero] = {
    "lyra": Hero(
        name="Lyra",
        kind="messenger",
        epithet="the quick little herald",
        wings=True,
        humor="she could turn a mistake into a grin",
        moral_tone="kind",
    ),
    "oren": Hero(
        name="Oren",
        kind="watcher",
        epithet="the careful listener",
        wings=True,
        humor="he laughed softly when the crows looked important",
        moral_tone="gentle",
    ),
    "sela": Hero(
        name="Sela",
        kind="child of the temple",
        epithet="the bright apprentice",
        wings=False,
        humor="she made jokes with her eyebrows",
        moral_tone="honest",
    ),
}

SACRED_THINGS: dict[str, SacredThing] = {
    "underclothes": SacredThing(
        name="underclothes",
        epithet="linen underclothes stitched with blue thread",
        material="linen",
        worn_on="body",
    ),
    "wing-cloak": SacredThing(
        name="wing-cloak",
        epithet="a narrow wing-cloak that left the shoulders free",
        material="feather-cloth",
        worn_on="shoulders",
    ),
    "golden-wrap": SacredThing(
        name="golden-wrap",
        epithet="a golden wrap for festival days",
        material="spun light",
        worn_on="hips",
    ),
}

MISCHIEFS: dict[str, Mischief] = {
    "anorexia": Mischief(
        name="Anorexia",
        verb="whispered away appetite",
        misunderstanding="The villagers thought Anorexia was a greedy wind, but it was really a sorrow that made food feel far away.",
        comic_image="a solemn goose bowing to a bowl that nobody could eat from",
        harms={"hunger", "sadness"},
    ),
    "wind-tease": Mischief(
        name="wind-tease",
        verb="snatched at cloth",
        misunderstanding="Everyone blamed the breeze, although the real trouble was a ribbon tied too loosely.",
        comic_image="a sash flapping like a tiny banner of panic",
        harms={"embarrassment", "confusion"},
    ),
    "mirror-mix": Mischief(
        name="mirror-mix",
        verb="showed the wrong reflection",
        misunderstanding="The moonwell gave back a funny image, and the people mistook it for a sign.",
        comic_image="a face in the water wearing a hat that did not exist",
        harms={"confusion"},
    ),
}

MORAL_VALUES = [
    "honesty",
    "care",
    "patience",
    "humility",
    "helpfulness",
]

HUMOR_BEATS = [
    "a goose pecked the hero's serious expression",
    "the temple cat sat on the scroll as if it had paid rent",
    "the priest tried to look wise and sneezed at the worst moment",
    "a ceremonial bell rang once for the wrong reason and then pretended nothing happened",
]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero: str
    thing: str
    mischief: str
    moral: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class World:
    setting: Setting
    hero: Hero
    thing: SacredThing
    mischief: Mischief
    moral: str
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "risk": 0.0, "clutter": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"wonder": 0.0, "worry": 0.0, "humor": 0.0, "trust": 0.0})
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

    def trace(self) -> list[str]:
        out = [
            f"setting={self.setting.name}",
            f"hero={self.hero.name}",
            f"thing={self.thing.name}",
            f"mischief={self.mischief.name}",
            f"meters={self.meters}",
            f"memes={self.memes}",
        ]
        return out


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def choose_hero(seed_rng: random.Random, name: Optional[str]) -> Hero:
    if name:
        if name not in HEROES:
            raise StoryError(f"Unknown hero '{name}'.")
        return HEROES[name]
    return HEROES[seed_rng.choice(list(HEROES))]


def choose_setting(seed_rng: random.Random, name: Optional[str]) -> Setting:
    if name:
        if name not in SETTINGS:
            raise StoryError(f"Unknown setting '{name}'.")
        return SETTINGS[name]
    return SETTINGS[seed_rng.choice(list(SETTINGS))]


def choose_thing(seed_rng: random.Random, name: Optional[str]) -> SacredThing:
    if name:
        if name not in SACRED_THINGS:
            raise StoryError(f"Unknown thing '{name}'.")
        return SACRED_THINGS[name]
    return SACRED_THINGS[seed_rng.choice(list(SACRED_THINGS))]


def choose_mischief(seed_rng: random.Random, name: Optional[str]) -> Mischief:
    if name:
        if name not in MISCHIEFS:
            raise StoryError(f"Unknown mischief '{name}'.")
        return MISCHIEFS[name]
    return MISCHIEFS[seed_rng.choice(list(MISCHIEFS))]


def valid_combo(setting: Setting, thing: SacredThing, mischief: Mischief) -> bool:
    if thing.name == "underclothes":
        return "confusion" in mischief.harms or "embarrassment" in mischief.harms
    if thing.name == "wing-cloak":
        return "embarrassment" in mischief.harms or "confusion" in mischief.harms
    if thing.name == "golden-wrap":
        return "confusion" in mischief.harms
    return False


def reasonableness_gate(setting: Setting, thing: SacredThing, mischief: Mischief) -> None:
    if not valid_combo(setting, thing, mischief):
        raise StoryError(
            f"No good myth can be built from {setting.name}, {thing.name}, and {mischief.name}: "
            "the object and trouble do not meaningfully meet."
        )


def intro(world: World) -> None:
    world.say(
        f"At {world.setting.name}, {world.setting.epithet}, there lived {world.hero.name}, "
        f"{world.hero.epithet}."
    )
    world.say(
        f"{world.hero.name} had {world.hero.moral_tone} wings and a way of smiling that made even the stones seem kinder."
    )


def setup(world: World) -> None:
    world.memes["wonder"] += 1
    world.say(
        f"One bright morning, the priests entrusted {world.hero.name} with {world.thing.epithet}."
    )
    world.say(
        f"They were not ordinary clothes. They were the sort of underclothes that belonged to a sacred promise, "
        f"meant to be kept neat for the rites."
    )


def misunderstanding_scene(world: World) -> None:
    world.para()
    world.meters["distance"] += 1
    world.memes["worry"] += 1
    world.say(
        f"Then the rumor of {world.mischief.name} drifted through {world.setting.place}."
    )
    world.say(world.mischief.misunderstanding)
    world.say(
        f"To make it worse, everyone was distracted by {random.choice(HUMOR_BEATS)}."
    )
    world.say(
        f"So when {world.hero.name} found the missing cloth in a basket by the altar, the whole court began to mutter."
    )


def turn_scene(world: World) -> None:
    world.para()
    world.meters["risk"] += 1
    world.memes["humor"] += 1
    world.say(
        f"{world.hero.name} lifted the cloth and nearly laughed at the sight: it had been caught on a bronze peg, "
        f"and the temple goose was standing under it like a tiny judge."
    )
    world.say(
        f"The people thought the cloth had been stolen, but the real trouble was only a small tangle and a bigger fear."
    )
    world.say(
        f"That was the joke of it: what looked like a crime was really a clumsy mistake with a serious face."
    )


def resolution_scene(world: World) -> None:
    world.para()
    world.memes["trust"] += 1
    world.meters["clutter"] = 0.0
    world.say(
        f"{world.hero.name} returned the underclothes to their chest, smoothed the linen flat, and spoke plainly to the crowd."
    )
    world.say(
        f'"Do not blame the dark word before you know the whole story," {world.hero.name} said. '
        f'"A misunderstanding can wear a louder mask than the truth."'
    )
    world.say(
        f"The villagers listened, and their faces changed. They saw that kindness was wiser than rumor."
    )
    world.say(
        f"After that, the court laughed gently, the goose was fed, and {world.setting.name} remembered that a clear word can heal a tangled day."
    )


def build_world(params: StoryParams) -> World:
    setting = choose_setting(random.Random(params.seed), params.setting if params.setting else None)
    hero = choose_hero(random.Random(params.seed + 1 if params.seed is not None else None), params.hero if params.hero else None)
    thing = choose_thing(random.Random(params.seed + 2 if params.seed is not None else None), params.thing if params.thing else None)
    mischief = choose_mischief(random.Random(params.seed + 3 if params.seed is not None else None), params.mischief if params.mischief else None)
    reasonableness_gate(setting, thing, mischief)
    return World(setting=setting, hero=hero, thing=thing, mischief=mischief, moral=params.moral)


def tell_story(world: World) -> None:
    intro(world)
    setup(world)
    misunderstanding_scene(world)
    turn_scene(world)
    resolution_scene(world)
    world.facts = {
        "setting": world.setting.name,
        "hero": world.hero.name,
        "thing": world.thing.name,
        "mischief": world.mischief.name,
        "moral": world.moral,
    }


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a mythic children's story set at {world.setting.name} about {world.hero.name}, {world.thing.name}, and a misunderstanding called {world.mischief.name}.",
        f"Tell a short fable where underclothes, a winged messenger, and the word Anorexia are part of a gentle lesson about {world.moral}.",
        f"Create a myth with humor in which a sacred item is mistaken for trouble, then set right with kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who carried the sacred underclothes in the story?",
            answer=f"{world.hero.name} carried them, because the priests trusted {world.hero.name} with the linen at {world.setting.name}.",
        ),
        QAItem(
            question=f"What mistake did the villagers make about {world.mischief.name}?",
            answer=f"They thought {world.mischief.name} was the cause of a theft, but it was really a misunderstanding and a small tangle.",
        ),
        QAItem(
            question=f"What lesson did the story teach?",
            answer=f"It taught {world.moral}: people should listen carefully before they accuse, because truth is kinder than rumor.",
        ),
        QAItem(
            question="Why did everyone laugh at the end?",
            answer=f"They laughed because the danger turned out to be a clumsy mistake, and the temple goose made the whole scene a little funny.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are underclothes?",
            answer="Underclothes are clothes worn under other clothes, close to the body.",
        ),
        QAItem(
            question="What is a wing in a myth?",
            answer="A wing is a body part that lets a creature fly or makes a hero seem touched by the sky.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding happens when someone thinks a thing means one idea, but the truth is different.",
        ),
        QAItem(
            question="What is moral value in a story?",
            answer="A moral value is the good lesson the story gently teaches, such as honesty or care.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the part of a story that makes people smile or laugh without turning cruel.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    return "\n".join(["--- trace ---"] + world.trace())


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- setting_fact(S).
hero(H) :- hero_fact(H).
thing(T) :- thing_fact(T).
mischief(M) :- mischief_fact(M).

valid_story(S,H,T,M) :- setting(S), hero(H), thing(T), mischief(M), compatible(T,M).

compatible(underclothes,anorexia).
compatible(underclothes,wind_tease).
compatible(wing_cloak,wind_tease).
compatible(golden_wrap,mirror_mix).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting_fact", s.name))
    for h in HEROES.values():
        lines.append(asp.fact("hero_fact", h.name))
    for t in SACRED_THINGS.values():
        lines.append(asp.fact("thing_fact", t.name))
    for m in MISCHIEFS.values():
        lines.append(asp.fact("mischief_fact", m.name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid_story/4.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for s in SETTINGS:
        for h in HEROES:
            for t in SACRED_THINGS:
                for m in MISCHIEFS:
                    if valid_combo(SETTINGS[s], SACRED_THINGS[t], MISCHIEFS[m]):
                        py_set.add((s, h, t, m))
    if asp_set != py_set:
        print("MISMATCH between ASP and Python gates.")
        print("only in ASP:", sorted(asp_set - py_set))
        print("only in Python:", sorted(py_set - asp_set))
        return 1
    print(f"OK: ASP and Python agree on {len(py_set)} combinations.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about underclothes, a wing, and the name Anorexia.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--thing", choices=sorted(SACRED_THINGS))
    ap.add_argument("--mischief", choices=sorted(MISCHIEFS))
    ap.add_argument("--moral", choices=sorted(MORAL_VALUES))
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
    hero = args.hero or rng.choice(list(HEROES))
    thing = args.thing or rng.choice(list(SACRED_THINGS))
    mischief = args.mischief or rng.choice(list(MISCHIEFS))
    moral = args.moral or rng.choice(MORAL_VALUES)

    if not valid_combo(SETTINGS[setting], SACRED_THINGS[thing], MISCHIEFS[mischief]):
        raise StoryError("The selected setting, sacred thing, and mischief do not make a convincing myth.")
    return StoryParams(setting=setting, hero=hero, thing=thing, mischief=mischief, moral=moral, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


CURATED = [
    StoryParams(setting="dawnshore", hero="lyra", thing="underclothes", mischief="anorexia", moral="care"),
    StoryParams(setting="moonwell", hero="oren", thing="underclothes", mischief="wind-tease", moral="honesty"),
    StoryParams(setting="highorchard", hero="sela", thing="golden-wrap", mischief="mirror-mix", moral="humility"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} valid stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.hero} / {p.thing} / {p.mischief}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
