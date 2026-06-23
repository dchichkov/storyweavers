#!/usr/bin/env python3
"""
storyworlds/worlds/equestrian_noodle_quest_nursery_rhyme.py
===========================================================

A small nursery-rhyme storyworld about an equestrian quest, a noodle mishap,
and a gentle ending that proves what changed.

The seed tale:
---
A little equestrian boy loved a noodle song.
One morning, he set out on a quest to bring back a silver noodle from the
meadow gate.
A small mare, a hummingbird helper, and a ribbon map joined the quest.
The noodle slipped into a puddle, the rider worried, and the helper showed a
safer way across the bridge.
At the end, the noodle was rescued, the quest was finished, and the little
team trotted home singing.

This script models a tiny quest domain with typed entities, accumulating
physical meters and emotional memes, state-driven narration, grounded QA, and
an ASP twin for the reasonableness gate.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SPLASH_MESS = "wet"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    plural: bool = False
    friendly: bool = False
    portable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "mare", "woman"}
        male = {"boy", "father", "dad", "man", "stallion"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class QuestSetting:
    place: str
    weather: str
    route: str
    affords: set[str] = field(default_factory=set)
    bridge: str = "the little bridge"


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    quest_value: str = "silver"
    at_risk_when: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    method: str
    safe_path: str
    encourages: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: QuestSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
    setting: str
    quest_item: str
    helper: str
    hero_name: str
    hero_gender: str
    companion_name: str
    companion_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": QuestSetting(place="the meadow", weather="mild", route="the ribbon path", affords={"quest"}),
    "lane": QuestSetting(place="the lane", weather="breezy", route="the cobble lane", affords={"quest"}),
    "stableyard": QuestSetting(place="the stableyard", weather="sunny", route="the straw gate", affords={"quest"}),
}

QUEST_ITEMS = {
    "noodle": QuestItem(
        id="noodle",
        label="noodle",
        phrase="a silver noodle",
        region="path",
        quest_value="silver",
        at_risk_when={"wet"},
    ),
    "ribbon": QuestItem(
        id="ribbon",
        label="ribbon",
        phrase="a bright ribbon",
        region="path",
        quest_value="bright",
        at_risk_when={"wet"},
    ),
}

HELPERS = {
    "bridge": Helper(
        id="bridge",
        label="bridge",
        phrase="a tiny bridge",
        method="cross the tiny bridge",
        safe_path="the little bridge",
        encourages="careful steps",
        covers={"path"},
        guards={"wet"},
    ),
    "pony": Helper(
        id="pony",
        label="pony",
        phrase="a small pony",
        method="follow the pony trail",
        safe_path="the pony trail",
        encourages="gentle steps",
        covers={"path"},
        guards={"wet"},
    ),
    "bucket": Helper(
        id="bucket",
        label="bucket",
        phrase="a wooden bucket",
        method="carry the buckle-bucket",
        safe_path="the dry lane",
        encourages="slow steps",
        covers={"path"},
        guards={"wet"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Rose", "Ava"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Ben", "Sam"]
TRAITS = ["lively", "gentle", "curious", "cheery"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for qi in QUEST_ITEMS:
            for h in HELPERS:
                if qi == "noodle" and h == "bridge":
                    combos.append((s, qi, h))
                if qi == "ribbon" and h in {"bridge", "pony"}:
                    combos.append((s, qi, h))
    return combos


def quest_at_risk(item: QuestItem, setting: QuestSetting) -> bool:
    return "quest" in setting.affords and "wet" in item.at_risk_when


def helper_fits(item: QuestItem, helper: Helper) -> bool:
    return item.region in helper.covers and item.at_risk_when <= helper.guards


def story_title(hero: Entity, item: Entity) -> str:
    return f"{hero.id} and the {item.label_word} quest"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    helper = f["helper"]
    return [
        f'Write a nursery-rhyme style story about an equestrian child named {hero.id} who goes on a quest for {item.label} and meets {helper.label}.',
        f'Write a gentle quest story that includes the words "equestrian" and "{item.label}", and ends with a safe crossing.',
        f"Tell a simple rhyming adventure where {hero.id} must rescue {item.phrase} with help from {helper.phrase}.",
    ]


def _do_quest(world: World, hero: Entity, item: Entity) -> None:
    hero.meters["quest"] += 1
    hero.memes["hope"] += 1
    item.meters["quest"] += 1


def _do_wet(world: World, hero: Entity, item: Entity) -> None:
    hero.meters["wet"] += 1
    item.meters["wet"] += 1
    hero.memes["worry"] += 1
    item.memes["lost"] += 1


def tell(setting: QuestSetting, item_cfg: QuestItem, helper_cfg: Helper,
         hero_name: str, hero_gender: str, companion_name: str, companion_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    quest_item = world.add(Entity(
        id=item_cfg.id, type=item_cfg.label, label=item_cfg.label, phrase=item_cfg.phrase,
        plural=item_cfg.plural, portable=True,
    ))
    helper = world.add(Entity(
        id=helper_cfg.id, type=helper_cfg.label, label=helper_cfg.label, phrase=helper_cfg.phrase,
        friendly=True, portable=False,
    ))

    world.facts["hero"] = hero
    world.facts["companion"] = companion
    world.facts["item"] = quest_item
    world.facts["helper"] = helper
    world.facts["setting"] = setting
    world.facts["helper_cfg"] = helper_cfg
    world.facts["item_cfg"] = item_cfg

    world.say(
        f"In the {setting.place}, there lived an equestrian child named {hero.id}, "
        f"who loved a noodle tune and a quest so bright."
    )
    world.say(
        f"{hero.id} and {companion.id} went out together on {setting.route}, "
        f"singing soft as a nursery light."
    )
    world.say(
        f"They carried {item_cfg.phrase}, for the quest asked for something small and sweet."
    )
    _do_quest(world, hero, quest_item)

    world.para()
    world.say(
        f"But the path grew damp, and the {item_cfg.label} slipped toward a puddle at their feet."
    )
    _do_wet(world, hero, quest_item)

    world.say(
        f"{companion.id} pointed to {helper_cfg.phrase}, and said, '{helper_cfg.encourages} will keep us neat.'"
    )
    world.say(
        f"So they chose to {helper_cfg.method}, and {item_cfg.label} stayed safe and dry."
    )

    world.para()
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"At last they found the way across, and {hero.id} lifted the {item_cfg.label} high."
    )
    world.say(
        f"The little team trotted home, the quest was done, and their noodle song rang bright."
    )
    world.facts["resolved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    item = f["item"]
    helper = f["helper"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who went on the quest in {setting.place}?",
            answer=f"{hero.id} went on the quest with {companion.id}. {hero.id} was the equestrian child in the story, and the two of them set out together.",
        ),
        QAItem(
            question=f"What happened when the {item.label} slipped toward the puddle?",
            answer=f"It got close to getting wet, so everyone worried for a moment. Then {companion.id} showed a safer way across, and the {item.label} stayed safe.",
        ),
        QAItem(
            question=f"How did {hero.id} and {companion.id} finish the quest?",
            answer=f"They followed {helper.phrase} and crossed carefully. After that, they trotted home with the {item.label}, and the quest was finished.",
        ),
        QAItem(
            question=f"Why did they choose {helper.label}?",
            answer=f"They chose {helper.label} because the path was damp and the quest item needed to stay dry. {helper.label.capitalize()} gave them a safer way forward.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an equestrian?",
            answer="An equestrian is a person who rides horses or loves horse riding. The word is often used for riding and horse care.",
        ),
        QAItem(
            question="What is a noodle?",
            answer="A noodle is a long, soft strip of food, often cooked in soup or sauce. It can also be a playful word in a song or story.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or solve a problem. In stories, a quest usually has a goal, a challenge, and a happy ending.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== Story Q&A ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="meadow", quest_item="noodle", helper="bridge", hero_name="Mia", hero_gender="girl", companion_name="Theo", companion_gender="boy"),
    StoryParams(setting="lane", quest_item="ribbon", helper="pony", hero_name="Leo", hero_gender="boy", companion_name="Nora", companion_gender="girl"),
]


def explain_rejection(item: QuestItem, helper: Helper) -> str:
    return f"(No story: {helper.label} does not make a fitting safe path for {item.label} in this quest.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest_item and args.helper:
        item = QUEST_ITEMS[args.quest_item]
        helper = HELPERS[args.helper]
        if not helper_fits(item, helper):
            raise StoryError(explain_rejection(item, helper))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest_item is None or c[1] == args.quest_item)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest_item, helper = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    companion_name = args.companion_name or rng.choice([n for n in (BOY_NAMES if companion_gender == "boy" else GIRL_NAMES) if n != hero_name])
    return StoryParams(
        setting=setting,
        quest_item=quest_item,
        helper=helper,
        hero_name=hero_name,
        hero_gender=hero_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    item = QUEST_ITEMS.get(params.quest_item)
    helper = HELPERS.get(params.helper)
    if setting is None or item is None or helper is None:
        raise StoryError("Invalid parameters.")
    if not quest_at_risk(item, setting) or not helper_fits(item, helper):
        raise StoryError(explain_rejection(item, helper))
    world = tell(setting, item, helper, params.hero_name, params.hero_gender, params.companion_name, params.companion_gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme quest storyworld with an equestrian noodle adventure.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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


ASP_RULES = r"""
valid(S,I,H) :- setting(S), item(I), helper(H), quest_risk(S,I), helper_fits(I,H).
quest_risk(S,I) :- setting(S), item(I), setting_affords(S,quest), item_risk(I,wet).
helper_fits(I,H) :- item(I), helper(H), helper_covers(H,path), helper_guards(H,wet).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_id, s in SETTINGS.items():
        lines.append(asp.fact("setting", s_id))
        for a in sorted(s.affords):
            lines.append(asp.fact("setting_affords", s_id, a))
    for i_id, i in QUEST_ITEMS.items():
        lines.append(asp.fact("item", i_id))
        for risk in sorted(i.at_risk_when):
            lines.append(asp.fact("item_risk", i_id, risk))
    for h_id, h in HELPERS.items():
        lines.append(asp.fact("helper", h_id))
        for c in sorted(h.covers):
            lines.append(asp.fact("helper_covers", h_id, c))
        for g in sorted(h.guards):
            lines.append(asp.fact("helper_guards", h_id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return

    rng_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng_seed + i))
            params.seed = rng_seed + i
            try:
                sample = generate(params)
            except StoryError:
                i += 1
                continue
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest_item} quest in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
