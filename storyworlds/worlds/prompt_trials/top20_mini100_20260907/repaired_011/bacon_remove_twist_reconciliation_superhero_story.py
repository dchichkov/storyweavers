#!/usr/bin/env python3
"""
A small superhero storyworld about a bacon mishap, a twist, and a reconciliation.

Seed premise:
A kid-friendly superhero scene begins with bacon that should be removed from a lunch plate, but the task turns into a twist when a helper misunderstands the plan. A brief conflict follows, then the characters talk it through and reconcile, ending with a cleaner plate and a kinder team.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    helper: str
    villain: str
    setting: str
    bacon_place: str
    remove_target: str = "bacon"
    twist: int = 0
    reconciliation: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


HEROS = ["Captain Nova", "Ruby Ray", "Silver Sprint", "Mighty Mint", "Star Shield", "Lightning Lily"]
SIDEKICKS = ["Pip", "June", "Theo", "Mara", "Finn", "Nia"]
HELPERS = ["Milo", "Tess", "Owen", "Bea", "Zeke", "Luna"]
VILLAINS = ["Captain Crumble", "The Grease Goblin", "Doctor Drip", "Sir Sizzle", "The Sneaky Smudge"]
SETTINGS = [
    "the sunny cafeteria",
    "the rooftop lunch garden",
    "the school kitchen",
    "the cozy hero headquarters",
    "the city park picnic table",
]
BACON_PLACES = [
    "on the sandwich",
    "beside the salad",
    "on the tray",
    "under the bun",
    "next to the fruit cup",
]

ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

hero_name(H) :- hero(H).
sidekick_name(S) :- sidekick(S).
helper_name(H) :- helper(H).
villain_name(V) :- villain(V).
setting_name(S) :- setting(S).
bacon_place_name(B) :- bacon_place(B).

valid(H, S) :- hero(H), setting(S).
valid_story(H, S, B) :- hero(H), setting(S), bacon_place(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for h in HEROS:
        lines.append(asp.fact("hero", h))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick", s))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for v in VILLAINS:
        lines.append(asp.fact("villain", v))
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for b in BACON_PLACES:
        lines.append(asp.fact("bacon_place", b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


TWISTS = [
    "The helper thought 'remove' meant hide the bacon, so they tucked it under a napkin instead of taking it away.",
    "A gust from the open window slid the bacon toward the edge, and everybody had to act fast.",
    "The villain swapped the serving tongs, so the wrong plate got the bacon by mistake.",
    "The sidekick shouted that the bacon was the clue, not the problem, which changed the plan in an instant.",
    "The hero discovered the bacon was stuck to a sticker, not the tray, and needed careful peeling.",
]

RECONCILIATIONS = [
    "Captain Nova smiled and said, 'Let's fix it together.' The helper nodded, and they cleaned the tray side by side.",
    "The sidekick apologized for the mix-up, and the hero answered, 'Mistakes happen when we hurry.' That made the whole table soften.",
    "The villain dropped the sneer and offered a cloth, saying, 'I can help put things right.' Everyone agreed to start over.",
    "The helper said, 'I heard remove, but I guessed wrong.' Captain Nova replied, 'Thanks for telling the truth. Now we know the next step.'",
    "After a deep breath, the team laughed at the confusion and made a new plan that everyone understood.",
]

OPENINGS = [
    "{hero} stood at {setting} with {sidekick} and {helper}, guarding a plate that had {bacon_place}.",
    "At {setting}, {hero} and {sidekick} were ready for lunch when {helper} pointed at the {remove_target} and frowned.",
    "It was a busy day at {setting}, and {hero} had one simple mission: remove the {remove_target} without causing a fuss.",
    "{hero} arrived at {setting} just in time to see {sidekick} and {helper} arguing over the {remove_target}.",
]

ENDING_IMAGES = [
    "In the end, the plate was neat, the bacon was removed, and the lunch crowd cheered for the calm rescue.",
    "By the last bite, the tray was clean and shiny, and the friends stood together like a true superhero team.",
    "The sun warmed the table while the empty space where the bacon had been showed how well they had fixed the problem.",
    "When the meal was done, the heroes shared a grin, because the small trouble had turned into a bigger friendship.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with bacon, a twist, and reconciliation.")
    ap.add_argument("--hero", choices=HEROS)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bacon-place", choices=BACON_PLACES, dest="bacon_place")
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
    hero = args.hero or rng.choice(HEROS)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    helper = args.helper or rng.choice(HELPERS)
    villain = args.villain or rng.choice(VILLAINS)
    setting = args.setting or rng.choice(SETTINGS)
    bacon_place = args.bacon_place or rng.choice(BACON_PLACES)

    if hero == sidekick:
        raise StoryError("No story: the hero and sidekick need to be different characters.")
    if hero == helper:
        raise StoryError("No story: the hero and helper need to be different characters.")
    if sidekick == helper:
        raise StoryError("No story: the sidekick and helper need to be different characters.")

    return StoryParams(
        hero=hero,
        sidekick=sidekick,
        helper=helper,
        villain=villain,
        setting=setting,
        bacon_place=bacon_place,
        twist=rng.randrange(len(TWISTS)),
        reconciliation=rng.randrange(len(RECONCILIATIONS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.twist = seed % len(TWISTS)
    params.reconciliation = (seed // len(TWISTS)) % len(RECONCILIATIONS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "hero": params.hero,
        "sidekick": params.sidekick,
        "helper": params.helper,
        "villain": params.villain,
        "setting": params.setting,
        "bacon_place": params.bacon_place,
        "remove_target": params.remove_target,
    }

    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", label=params.hero, meters={"alertness": 1.0}, memes={"duty": 1.0}))
    sidekick = w.add(Entity(id=params.sidekick, kind="character", label=params.sidekick, memes={"worry": 0.4}))
    helper = w.add(Entity(id=params.helper, kind="character", label=params.helper, memes={"confusion": 0.6}))
    villain = w.add(Entity(id=params.villain, kind="character", label=params.villain, memes={"scheming": 0.7}))
    bacon = w.add(Entity(id="bacon", kind="food", label="bacon", meters={"grease": 0.8}, memes={"temptation": 0.5}))
    tray = w.add(Entity(id="tray", kind="object", label="tray", meters={"cleanliness": 0.3}, memes={"task": 1.0}))

    w.say(OPENINGS[(params.twist + 1) % len(OPENINGS)].format(**values))
    w.say(f"The bacon looked shiny and tempting, but {hero.label} kept a steady voice and said the bacon had to be removed before lunch could begin.")
    w.say(f"{sidekick.label} whispered, 'I can help.' {helper.label} answered, 'Then tell me exactly what remove means.'")

    w.para()
    twist_text = TWISTS[params.twist % len(TWISTS)]
    w.say(twist_text)
    w.say(f"That twist made {helper.label} gasp and {sidekick.label} point at the plate while {villain.label} tried to sneak closer.")
    w.say(f"{hero.label} raised a hand and said, 'Wait. We need to talk before we move anything.'")

    w.para()
    hero.meters["alertness"] = 1.2
    sidekick.memes["worry"] = 0.1
    helper.memes["confusion"] = 0.2
    villain.memes["scheming"] = 0.1
    bacon.meters["grease"] = 0.0
    tray.meters["cleanliness"] = 0.9
    w.say(RECONCILIATIONS[params.reconciliation % len(RECONCILIATIONS)])
    w.say(f"{helper.label} said, 'I get it now. I should remove the bacon from the tray, not hide it.' {hero.label} nodded and replied, 'Exactly.'")
    w.say(f"{sidekick.label} added, 'And nobody has to do it alone.' So the team lifted the bacon away, wiped the tray, and set the lunch right.")

    w.para()
    w.say(ENDING_IMAGES[(params.twist + params.reconciliation) % len(ENDING_IMAGES)])
    w.say(f"{hero.label}, {sidekick.label}, and {helper.label} shared a quick grin while {villain.label} quietly backed off, no longer causing trouble.")

    w.facts.update(
        hero=hero.id,
        sidekick=sidekick.id,
        helper=helper.id,
        villain=villain.id,
        setting=params.setting,
        bacon_place=params.bacon_place,
        twist=TWISTS[params.twist % len(TWISTS)],
        reconciliation=RECONCILIATIONS[params.reconciliation % len(RECONCILIATIONS)],
        bacon_removed=True,
    )

    prompts = [
        "Write a superhero story about bacon that must be removed, but a twist causes a misunderstanding before everyone reconciles.",
        f"Tell a child-friendly superhero story set at {params.setting} with {params.hero}, {params.sidekick}, and {params.helper}.",
        f"Write a story where the team needs to remove bacon, the plan goes wrong, and a calm reconciliation fixes it.",
    ]

    story_qa = [
        QAItem(
            question="What was the team trying to do at the beginning?",
            answer=f"They were trying to remove the bacon from the {params.bacon_place} so lunch could start cleanly.",
        ),
        QAItem(
            question="What caused the twist in the story?",
            answer=f"The twist happened when {twist_text.lower()}",
        ),
        QAItem(
            question="How did the characters reconcile?",
            answer=f"They talked clearly, apologized for the mix-up, and worked together to remove the bacon and clean the tray.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="By the end, the bacon was removed, the tray was clean, and the team felt closer and calmer.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to make peace after a misunderstanding or disagreement.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the characters expected.",
        ),
        QAItem(
            question="Why do superheroes need teamwork?",
            answer="Superheroes need teamwork because shared plans and clear talking help them solve problems safely.",
        ),
        QAItem(
            question="Why is bacon in this storyworld?",
            answer="Bacon is the small object that creates the problem the heroes need to remove.",
        ),
    ]

    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="Captain Nova", sidekick="Pip", helper="Milo", villain="Captain Crumble", setting="the sunny cafeteria", bacon_place="on the sandwich", twist=0, reconciliation=0),
    StoryParams(hero="Ruby Ray", sidekick="June", helper="Tess", villain="The Grease Goblin", setting="the rooftop lunch garden", bacon_place="beside the salad", twist=1, reconciliation=3),
    StoryParams(hero="Silver Sprint", sidekick="Theo", helper="Owen", villain="Doctor Drip", setting="the school kitchen", bacon_place="on the tray", twist=2, reconciliation=2),
    StoryParams(hero="Lightning Lily", sidekick="Mara", helper="Luna", villain="Sir Sizzle", setting="the cozy hero headquarters", bacon_place="under the bun", twist=4, reconciliation=1),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_curated() -> list[StoryParams]:
    return CURATED


def valid_combos() -> list[tuple[str, str]]:
    return [(h, s) for h in HEROS for s in SETTINGS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted({(h, s) for h, s in asp.atoms(model, "valid")})


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (hero, setting) combos:\n")
        for hero, setting in triples:
            print(f"  {hero:18} -> {setting}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in build_curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
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
            header = f"### {p.hero}: bacon at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
