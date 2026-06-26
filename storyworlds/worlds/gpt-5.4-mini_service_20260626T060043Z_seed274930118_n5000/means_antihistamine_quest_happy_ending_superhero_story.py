#!/usr/bin/env python3
"""
storyworlds/worlds/means_antihistamine_quest_happy_ending_superhero_story.py
=============================================================================

A standalone superhero story world about a small quest, an allergy scare, and a
happy ending. The domain is deliberately narrow: a hero, a helper, a mission,
a troublesome sneeze/allergy problem, and a reasonable means to fix it with
antihistamine.

Seed tale sketch:
---
Captain Comet wants to protect the city, but a burst of pollen keeps making him
sneeze at the worst possible time. When a little mission to deliver a lost comic
book turns into a quest across the city, his partner worries that he cannot do
it while sniffling and rubbing his eyes. They use the right means: they stop at
the clinic, get antihistamine, and the hero finishes the quest with a happy
ending.
---

This script turns that premise into a tiny simulated world with physical meters
and emotional memes, a causal turn, and a resolution that proves the change.
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "hero"}
        female = {"girl", "woman", "mother", "mom", "heroine"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the city"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    danger: str
    route: str
    means_needed: str
    keyword: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    helps: set[str]
    is_means: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    quest_state: str = "start"

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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.quest_state = self.quest_state
        return w


def _r_allergy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("Hero")
    if not hero:
        return out
    if hero.meters.get("pollen", 0) < THRESHOLD:
        return out
    if hero.memes.get("allergy", 0) >= THRESHOLD:
        sig = ("allergy", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        out.append(f"{hero.id} kept sneezing and rubbing {hero.pronoun('possessive')} eyes.")
    return out


def _r_hinder(world: World) -> list[str]:
    hero = world.entities.get("Hero")
    sidekick = world.entities.get("Sidekick")
    if not hero or not sidekick:
        return []
    if hero.memes.get("worry", 0) < THRESHOLD:
        return []
    sig = ("hinder", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sidekick.memes["concern"] = sidekick.memes.get("concern", 0) + 1
    return [f"{sidekick.id} frowned, because the mission needed a steady hero."]


def _r_remedy(world: World) -> list[str]:
    hero = world.entities.get("Hero")
    med = world.entities.get("Antihistamine")
    if not hero or not med:
        return []
    if hero.memes.get("allergy", 0) < THRESHOLD:
        return []
    if hero.meters.get("took_antihistamine", 0) < THRESHOLD:
        return []
    sig = ("remedy", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] = 0
    hero.meters["pollen"] = 0
    return [f"The antihistamine helped {hero.id} breathe easy again."]


RULES = [_r_allergy, _r_hinder, _r_remedy]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_resolve(world: World) -> bool:
    sim = world.copy()
    hero = sim.get("Hero")
    med = sim.get("Antihistamine")
    hero.meters["took_antihistamine"] = 1
    hero.memes["allergy"] = 1
    propagate(sim, narrate=False)
    return hero.memes.get("worry", 0) == 0 or med is not None


@dataclass
class StoryParams:
    place: str
    hero_name: str
    sidekick_name: str
    villain_name: str
    quest: str
    remedy: str
    seed: Optional[int] = None


SETTINGS = {
    "city": Setting(place="the city", affords={"rescue", "deliver", "hunt"}),
    "clinic": Setting(place="the clinic", affords={"recover", "deliver"}),
    "rooftops": Setting(place="the rooftops", affords={"rescue", "hunt"}),
}

QUESTS = {
    "comic_delivery": Quest(
        id="comic_delivery",
        goal="deliver the lost comic book",
        danger="the pollen in the air",
        route="from the library to the museum",
        means_needed="antihistamine",
        keyword="quest",
        tags={"quest", "comic", "pollen"},
    ),
    "cat_rescue": Quest(
        id="cat_rescue",
        goal="rescue the kitten from the bell tower",
        danger="a sneezing fit",
        route="up the old stairs",
        means_needed="antihistamine",
        keyword="quest",
        tags={"quest", "rescue", "cat"},
    ),
    "crown_return": Quest(
        id="crown_return",
        goal="return the mayor's golden crown",
        danger="pollen drifting from the park",
        route="across the bridge",
        means_needed="antihistamine",
        keyword="quest",
        tags={"quest", "crown", "pollen"},
    ),
}

REMEDIES = {
    "antihistamine": Remedy(
        id="antihistamine",
        label="antihistamine",
        phrase="a small dose of antihistamine",
        helps={"pollen", "sneeze", "allergy"},
    )
}

HERO_NAMES = ["Captain Comet", "Starlight", "Thunder Ace", "Rocket Rose", "Night Spark"]
SIDEKICK_NAMES = ["Mira", "Jasper", "Nia", "Toby", "Luna"]
VILLAIN_NAMES = ["Doctor Dust", "Pollen King", "The Sneezes", "Captain Cough"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, qid, rid) for place in SETTINGS for qid in QUESTS for rid in REMEDIES]


def explain_rejection(place: str, quest: Quest, remedy: Remedy) -> str:
    return f"(No story: the {quest.goal} needs {remedy.label}, and this world can only tell that kind of superhero tale at {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero quest story world with a happy ending and antihistamine means."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.remedy:
        combos = [c for c in combos if c[2] == args.remedy]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, qid, rid = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    return StoryParams(place=place, hero_name=hero, sidekick_name=sidekick, villain_name=villain, quest=qid, remedy=rid)


def introduce(world: World, hero: Entity, sidekick: Entity, villain: Entity, quest: Quest) -> None:
    world.say(f"{hero.id} was a brave superhero who always wanted to do the right thing.")
    world.say(f"{sidekick.id} flew beside {hero.pronoun('object')} on patrol, while {villain.id} schemed across {world.setting.place}.")
    world.say(f"That day, their {quest.keyword} was to {quest.goal} {quest.route}.")


def trigger_problem(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["pollen"] = 1
    hero.memes["allergy"] = 1
    world.say(f"Then the air filled with {quest.danger}, and {hero.id} started to sneeze.")
    propagate(world, narrate=True)


def warn_and_choose_means(world: World, hero: Entity, sidekick: Entity, remedy: Remedy) -> None:
    hero.memes["worry"] = 1
    world.say(f"{sidekick.id} said the mission needed a better means than guessing and rushing ahead.")
    world.say(f'They found the right means: {remedy.phrase}.')
    hero.meters["took_antihistamine"] = 1
    world.say(f"{hero.id} took the antihistamine, and the sneezing eased up.")


def finish_quest(world: World, hero: Entity, sidekick: Entity, quest: Quest) -> None:
    propagate(world, narrate=True)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0) + 1
    world.say(f"With a clear head, {hero.id} finished the {quest.keyword} and completed the mission.")
    world.say(f"{sidekick.id} cheered, and the city got its lost treasure back.")
    world.say(f"It was a happy ending: {hero.id} stood tall again, strong and smiling.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="Hero", kind="character", type="hero", label=params.hero_name))
    sidekick = world.add(Entity(id="Sidekick", kind="character", type="hero", label=params.sidekick_name))
    villain = world.add(Entity(id="Villain", kind="character", type="hero", label=params.villain_name))
    quest = QUESTS[params.quest]
    remedy = REMEDIES[params.remedy]
    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, quest=quest, remedy=remedy, setting=world.setting)

    introduce(world, hero, sidekick, villain, quest)
    world.para()
    trigger_problem(world, hero, quest)
    world.say(f"{villain.id} hoped the distraction would stop the {quest.goal}.")
    world.para()
    warn_and_choose_means(world, hero, sidekick, remedy)
    world.say(f"It was the perfect means for the quest, because {remedy.label} helped with the allergy.")
    world.para()
    finish_quest(world, hero, sidekick, quest)
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    remedy = f["remedy"]
    return [
        f'Write a short superhero story for a child about a {quest.keyword} and the word "{remedy.label}".',
        f"Tell a gentle quest story where {hero.label} has an allergy, needs antihistamine, and still saves the day.",
        f"Write a happy-ending superhero tale about using the right means to finish a mission.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    quest = f["quest"]
    remedy = f["remedy"]
    return [
        QAItem(
            question=f"What was the superhero quest?",
            answer=f"The quest was to {quest.goal}. It became harder because {quest.danger} made {hero.id} sneeze.",
        ),
        QAItem(
            question=f"What means did they use to help {hero.label} keep going?",
            answer=f"They used {remedy.label}. That helped {hero.id} breathe easier and finish the mission.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and {sidekick.label}?",
            answer=f"It ended happily. {hero.id} finished the quest, {sidekick.id} cheered, and the city was saved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to do something important, like rescue, deliver, or return something lost.",
        ),
        QAItem(
            question="What is antihistamine for?",
            answer="Antihistamine is medicine that can help with allergies, sneezing, and itchy eyes.",
        ),
        QAItem(
            question="Why is having a means important in a story?",
            answer="A means is the way a character solves a problem, so the story can move from trouble to a good ending.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.kind:7}) meters={meters} memes={memes}")
    lines.append(f"  quest_state={world.quest_state}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- hero_name(X).
quest(Q) :- quest_id(Q).
remedy(R) :- remedy_id(R).

valid_story(P, Q, R) :- place(P), quest(Q), remedy(R).
needs_means(Q, R) :- quest(Q), remedy(R), remedy_helps(R, pollen).
has_happy_ending(P, Q, R) :- valid_story(P, Q, R), needs_means(Q, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for qid in QUESTS:
        lines.append(asp.fact("quest_id", qid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy_id", rid))
        for h in sorted(r.helps):
            lines.append(asp.fact("remedy_helps", rid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("city", "Captain Comet", "Mira", "Doctor Dust", "comic_delivery", "antihistamine"),
            StoryParams("clinic", "Starlight", "Nia", "Pollen King", "cat_rescue", "antihistamine"),
            StoryParams("rooftops", "Thunder Ace", "Luna", "Captain Cough", "crown_return", "antihistamine"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
