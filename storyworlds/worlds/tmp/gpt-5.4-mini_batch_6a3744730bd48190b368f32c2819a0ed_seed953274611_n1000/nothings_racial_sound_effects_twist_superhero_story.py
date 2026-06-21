#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nothings_racial_sound_effects_twist_superhero_story.py
======================================================================================

A standalone storyworld for a tiny superhero tale with sound effects and a twist.

Premise:
- A young hero chases a sneaky trickster through a city block.
- Loud comic-book sound effects punctuate the action.
- The twist reveals the "villain" was actually testing a harmless rescue plan.
- The story includes the seed words "nothings" and "racial" in-world as words
  the characters notice on a mysterious flyer.

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports shared results eagerly
- imports shared asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    noisy: bool = False
    helpful: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class HeroPack:
    id: str
    title: str
    cape: str
    move: str
    sparkle: str


@dataclass
class TwistBeat:
    id: str
    reveal: str
    turn: str
    rescue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    sound: str
    source: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    hero: Entity
    friend: Entity
    adult: Entity
    pack: HeroPack
    twist: TwistBeat
    signals: list[Signal]
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return World(
            hero=copy.deepcopy(self.hero),
            friend=copy.deepcopy(self.friend),
            adult=copy.deepcopy(self.adult),
            pack=copy.deepcopy(self.pack),
            twist=copy.deepcopy(self.twist),
            signals=copy.deepcopy(self.signals),
            facts=copy.deepcopy(self.facts),
            fired=set(self.fired),
            paragraphs=[[]],
        )


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    adult: str
    adult_gender: str
    pack: str
    twist: str
    signal1: str
    signal2: str
    seed: Optional[int] = None


HEROES = {
    "starling": HeroPack("starling", "Starling", "blue cape", "zip across the rooftops", "sparkly"),
    "comet": HeroPack("comet", "Comet", "red cape", "vault over the taxi", "bright"),
    "whirl": HeroPack("whirl", "Whirl", "green cape", "spin around the corner", "quick"),
}

TWISTS = {
    "decoy": TwistBeat(
        id="decoy",
        reveal="the scrap of paper was not a threat at all",
        turn="it was a map to the old clock tower",
        rescue="the hero found the missing kitten and the lost kite",
        tags={"twist", "map"},
    ),
    "practice": TwistBeat(
        id="practice",
        reveal="the loud mask was only part of a practice drill",
        turn="the stranger was training for a rescue day",
        rescue="everyone learned the safe hand signal and the route out",
        tags={"twist", "practice"},
    ),
    "helper": TwistBeat(
        id="helper",
        reveal="the 'villain' was really a helper in a patchy coat",
        turn="the helper wanted the alley cleared before rain started",
        rescue="the hero carried boxes to a dry place and saved the candy stand",
        tags={"twist", "helper"},
    ),
}

SIGNALS = {
    "bam": Signal("bam", "BAM", "BAM!", "the comic book window", tags={"sound"}),
    "wham": Signal("wham", "WHAM", "WHAM!", "the rooftop door", tags={"sound"}),
    "zap": Signal("zap", "ZAP", "ZAP!", "the blinking gadget", tags={"sound"}),
    "whoosh": Signal("whoosh", "WHOOSH", "WHOOSH!", "the cape", tags={"sound"}),
}

GIRL_NAMES = ["Mia", "Zoe", "Ava", "Nora", "Lily", "Ella"]
BOY_NAMES = ["Max", "Leo", "Finn", "Theo", "Eli", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero storyworld with sound effects and a twist.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--signal1", choices=SIGNALS)
    ap.add_argument("--signal2", choices=SIGNALS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--adult")
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for h in HEROES:
        for t in TWISTS:
            for s1 in SIGNALS:
                for s2 in SIGNALS:
                    if s1 != s2:
                        combos.append((h, t, s1, s2))
    return combos


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.twist:
        pass
    combos = [c for c in valid_combos()
              if (args.hero is None or c[0] == args.hero)
              and (args.twist is None or c[1] == args.twist)
              and (args.signal1 is None or c[2] == args.signal1)
              and (args.signal2 is None or c[3] == args.signal2)]
    if not combos:
        raise StoryError("(No valid combo matches the given options.)")
    hero, twist, signal1, signal2 = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    name = args.name or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=name)
    adult = args.adult or rng.choice(["Mom", "Dad"])
    return StoryParams(
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        adult=adult,
        adult_gender="mother" if adult == "Mom" else "father",
        pack=hero,
        twist=twist,
        signal1=signal1,
        signal2=signal2,
    )


def reasonableness_gate(params: StoryParams) -> bool:
    return params.signal1 != params.signal2 and params.hero in HEROES and params.twist in TWISTS


def _do_twist(world: World) -> None:
    key = ("twist", world.twist.id)
    if key in world.fired:
        return
    world.fired.add(key)
    world.hero.memes["surprise"] = world.hero.memes.get("surprise", 0) + 1
    world.friend.memes["surprise"] = world.friend.memes.get("surprise", 0) + 1


def tell(params: StoryParams) -> World:
    pack = HEROES[params.hero]
    twist = TWISTS[params.twist]
    hero = Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero")
    friend = Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend")
    adult = Entity(id=params.adult, kind="character", type=params.adult_gender, role="adult")
    signals = [SIGNALS[params.signal1], SIGNALS[params.signal2]]
    world = World(hero=hero, friend=friend, adult=adult, pack=pack, twist=twist, signals=signals)

    hero.memes["brave"] = 1.0
    friend.memes["curious"] = 1.0
    adult.memes["calm"] = 1.0

    world.say(
        f"On a busy afternoon, {hero.id} wore {pack.cape} and tried to be a city superhero. "
        f"{friend.id} dashed along beside {hero.pronoun('object')}, and the air buzzed with comic-book excitement."
    )
    world.say(
        f"{signals[0].sound} {signals[1].sound} {pack.sparkle.capitalize()} little sound effects bounced from {signals[0].source} and {signals[1].source}. "
        f"{hero.id} loved the noise, but a strange flyer on a mailbox said nothings about a racial gala downtown."
    )

    world.para()
    hero.memes["worry"] = 1.0
    world.say(
        f"{hero.id} squinted at the flyer. \"That doesn't make sense,\" {hero.pronoun()} said. "
        f"\"It talks about nothings and a racial banner, but the street is quiet.\""
    )
    world.say(
        f"{friend.id} pointed to the alley. \"Maybe the clue is there,\" {friend.pronoun()} whispered."
    )

    world.para()
    _do_twist(world)
    world.say(
        f"Then came the twist: {twist.reveal}. {twist.turn}. "
        f"{signals[1].sound} went the gadget, and {signals[0].sound} answered from the door."
    )
    if twist.id == "practice":
        world.say(
            f"The so-called villain stepped out with a clipboard and a grin. \"You found the safety route,\" {adult.id} said, proud and relieved."
        )
    elif twist.id == "decoy":
        world.say(
            f"The paper fluttered away, and under it was a tiny arrow pointing to help instead of harm."
        )
    else:
        world.say(
            f"The patchy-coat helper waved from the corner and asked for a hand, not a fight."
        )

    world.para()
    world.say(
        f"{adult.id} came running when the noise grew loud. {adult.pronoun().capitalize()} did not scold them. "
        f"Instead, {adult.pronoun()} praised {hero.id} for calling out the trouble and checking the clue."
    )
    world.say(
        f"By the end, {twist.rescue}. {hero.id}'s cape {pack.move} {signals[1].sound} {signals[0].sound}, and the whole block felt safe again."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        pack=pack,
        twist=twist,
        signals=signals,
        outcome=twist.id,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a superhero story for a child that includes the words nothings and racial, plus loud sound effects and a twist.",
        f"Tell a short comic-book adventure where {world.hero.id} hears strange clues, says nothings aloud, and discovers a twist instead of a real danger.",
        f"Write a playful superhero story with BAM and WHOOSH sound effects, and make the surprise ending gentle and clever.",
    ]


def story_qa(world: World) -> list[QAItem]:
    qas = [
        QAItem(
            question="What did the hero think the flyer meant at first?",
            answer="At first, the hero thought the flyer might be a warning about something serious. But the clue turned out to be confusing on purpose, so the hero had to look closer.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {world.twist.reveal}. That changed the whole feeling of the scene, because the story became about helping and checking clues instead of fighting a real villain.",
        ),
        QAItem(
            question="Why did the hero feel better at the end?",
            answer=f"The hero felt better because {world.twist.turn} and the grown-up praised the quick thinking. The sound effects stayed exciting, but nothing unsafe happened.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What do comic-book sound effects do in a story?",
            answer="They make the action feel louder and more exciting. Words like BAM, WHAM, ZAP, and WHOOSH help readers hear the energy in their heads.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought was happening. It can make a story feel fresh because the ending is not what you expected at first.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return (
        f"hero={world.hero.id} memes={dict(world.hero.memes)}\n"
        f"friend={world.friend.id} memes={dict(world.friend.memes)}\n"
        f"adult={world.adult.id} memes={dict(world.adult.memes)}\n"
        f"twist={world.twist.id} fired={sorted(world.fired)}"
    )


def generate(params: StoryParams) -> StorySample:
    if not reasonableness_gate(params):
        raise StoryError("(Invalid parameters for this storyworld.)")
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


CURATED = [
    StoryParams(
        hero="starling",
        hero_gender="girl",
        friend="Max",
        friend_gender="boy",
        adult="Mom",
        adult_gender="mother",
        pack="starling",
        twist="decoy",
        signal1="bam",
        signal2="whoosh",
    ),
    StoryParams(
        hero="comet",
        hero_gender="boy",
        friend="Mia",
        friend_gender="girl",
        adult="Dad",
        adult_gender="father",
        pack="comet",
        twist="practice",
        signal1="zap",
        signal2="wham",
    ),
    StoryParams(
        hero="whirl",
        hero_gender="girl",
        friend="Theo",
        friend_gender="boy",
        adult="Mom",
        adult_gender="mother",
        pack="whirl",
        twist="helper",
        signal1="whoosh",
        signal2="bam",
    ),
]


def build_asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_facts() -> str:
    import asp
    lines = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for sid in SIGNALS:
        lines.append(asp.fact("signal", sid))
    lines.append(asp.fact("requires_sound_twist", "yes"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(H, T, S1, S2) :- hero(H), twist(T), signal(S1), signal(S2), S1 != S2.
twist_story(T) :- twist(T).
sound_effect(S) :- signal(S).
"""


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(build_asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke test generated a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for h in HEROES:
        for t in TWISTS:
            for s1 in SIGNALS:
                for s2 in SIGNALS:
                    if s1 != s2:
                        combos.append((h, t, s1, s2))
    return combos


def resolve_name_pair(rng: random.Random) -> tuple[str, str]:
    g1 = rng.choice(["girl", "boy"])
    g2 = "boy" if g1 == "girl" else "girl"
    return _pick_name(rng, g1), _pick_name(rng, g2)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(build_asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
