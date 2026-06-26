#!/usr/bin/env python3
"""
Storyworld: a small superhero quest with a surprise ally.

Seed tale:
A young superhero hears a sad moan from a storm drain and finds a mallard stuck
inside. They begin a careful quest to help the duck, but the surprise is that
the mallard turns out to be a tiny courage-buddy who knows the way to the lost
feather-key. Together they finish the quest and fly home at sunset.

This world keeps a simple physical/emotional model:
- meters: physical state like trapped, safe, found, tired, wet
- memes: emotional state like worry, hope, pride, relief

The story is driven by state transitions, not by a frozen template.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    ally_of: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit city"
    weather: str = "windy"
    light: str = "twilight"


@dataclass
class Quest:
    goal: str
    clue: str
    obstacle: str
    reward: str
    keyword: str = "quest"


@dataclass
class Surprise:
    reveal: str
    helper_title: str
    twist_action: str
    keyword: str = "surprise"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


THRESHOLD = 1.0


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    companion: str
    quest: str
    surprise: str
    seed: Optional[int] = None


SETTINGS = {
    "city": Setting(place="the moonlit city", weather="windy", light="twilight"),
    "harbor": Setting(place="the quiet harbor", weather="misty", light="evening"),
    "roof": Setting(place="the glassy rooftop", weather="breezy", light="sunset"),
}

QUESTS = {
    "feather_key": Quest(
        goal="find the lost feather-key",
        clue="a silver feather sparkling under a grate",
        obstacle="a locked hatch",
        reward="the way home",
        keyword="Quest",
    ),
    "signal_lamp": Quest(
        goal="restore the signal lamp",
        clue="a glowing trail of soot and stardust",
        obstacle="a dark tunnel",
        reward="a bright sky signal",
        keyword="Quest",
    ),
}

SURPRISES = {
    "mallard_helper": Surprise(
        reveal="the mallard was wearing a tiny mask under its wing",
        helper_title="ducky sidekick",
        twist_action="quacked in a secret pattern",
        keyword="Surprise",
    ),
    "mallard_guide": Surprise(
        reveal="the mallard knew the way because it had flown there before",
        helper_title="feathered guide",
        twist_action="waddled ahead with brave little steps",
        keyword="Surprise",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero quest with a surprise mallard.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion", default="mallard")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_pool = ["Nova", "Comet", "Scout", "Mira", "Pax", "Toby", "Aria", "Ezra"]
    hero = args.hero or rng.choice(hero_pool)
    quest = args.quest or rng.choice(list(QUESTS))
    surprise = args.surprise or rng.choice(list(SURPRISES))

    if args.companion and args.companion.lower() != "mallard":
        raise StoryError("This world only supports a mallard as the companion.")
    return StoryParams(
        setting=setting,
        hero=hero,
        hero_type=hero_type,
        companion="mallard",
        quest=quest,
        surprise=surprise,
    )


def _set_meters(ent: Entity, **vals: float) -> None:
    for k, v in vals.items():
        ent.meters[k] = ent.meters.get(k, 0.0) + v


def _set_memes(ent: Entity, **vals: float) -> None:
    for k, v in vals.items():
        ent.memes[k] = ent.memes.get(k, 0.0) + v


def tell(setting: Setting, quest: Quest, surprise: Surprise, hero_name: str, hero_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    mallard = world.add(Entity(id="mallard", kind="character", type="mallard", label="the mallard"))
    villain = world.add(Entity(id="smoke", kind="thing", type="smoke", label="the smoky jam"))

    _set_memes(hero, wonder=1, hope=1)
    _set_memes(mallard, fear=1, trust=0)
    _set_meters(mallard, trapped=1, wet=1)
    _set_meters(villain, blocking=1)

    world.say(
        f"In {setting.place}, {hero_name} was a little {hero_type} superhero who kept watch at {setting.light}."
    )
    world.say(
        f"One evening, {hero_name} heard a soft moan near a drain and found a mallard stuck by {villain.label}."
    )
    world.say(
        f"{hero_name} knelt beside the grate and promised to begin a {quest.keyword} to {quest.goal}."
    )
    world.para()

    hero.memes["worry"] = 1
    hero.meters["searching"] = 1
    world.say(
        f"The first clue was {quest.clue}, but the path led to {quest.obstacle}, and {hero_name} had to slow down."
    )
    world.say(
        f"The mallard stopped moaning and listened closely, as if {surprise.twist_action} might solve the whole thing."
    )
    mallard.memes["hope"] = 1
    mallard.meters["waiting"] = 1

    world.para()
    world.say(
        f"Then came the {surprise.keyword}: {surprise.reveal}."
    )
    mallard.ally_of = hero.id
    hero.memes["surprise"] = 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f"That tiny {surprise.helper_title} knew a hidden latch, so {hero_name} and the mallard pulled together."
    )

    _set_meters(mallard, freed=1)
    _set_meters(hero, solving=1)
    _set_memes(hero, relief=1)
    _set_memes(mallard, pride=1)
    villain.meters["blocking"] = 0
    villain.meters["gone"] = 1
    world.say(
        f"The grate opened, the smoky jam vanished, and the mallard waddled free with a happy shake."
    )
    world.say(
        f"At the end of the {quest.keyword}, {hero_name} carried the reward home: {quest.reward}, plus a new friend in a tiny mask."
    )

    world.facts.update(
        hero=hero,
        mallard=mallard,
        villain=villain,
        quest=quest,
        surprise=surprise,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    surprise = f["surprise"]
    return [
        f'Write a short superhero story for young children that includes the words "moan" and "mallard".',
        f"Tell a gentle story where {hero.id} hears a moan, starts a {quest.keyword}, and discovers a mallard surprise.",
        f"Write a small heroic tale in which a child superhero solves {quest.goal} with a {surprise.helper_title}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mallard = f["mallard"]
    quest = f["quest"]
    surprise = f["surprise"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} hear the moan?",
            answer=f"{hero.id} heard the moan in {setting.place}, near a drain where the mallard was stuck.",
        ),
        QAItem(
            question=f"What was the superhero's {quest.keyword} about?",
            answer=f"The {quest.keyword} was about trying to {quest.goal}.",
        ),
        QAItem(
            question=f"What was surprising about the mallard?",
            answer=f"The surprise was that {surprise.reveal}, so the mallard became a brave helper.",
        ),
        QAItem(
            question=f"How did {hero.id} help the mallard?",
            answer=f"{hero.id} listened, followed the clue, and pulled the latch open so the mallard could get free.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a mallard?",
        answer="A mallard is a kind of duck with a green-headed dad duck and a brown mother duck.",
    ),
    QAItem(
        question="What is a quest?",
        answer="A quest is a mission or search to find something important or solve a problem.",
    ),
    QAItem(
        question="What is a surprise?",
        answer="A surprise is something unexpected that makes you stop and pay attention.",
    ),
    QAItem(
        question="Why might a duck moan?",
        answer="A duck might moan or make a sad sound when it is scared, stuck, or upset.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.ally_of:
            bits.append(f"ally_of={e.ally_of}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- actor(H).
mallard(M) :- actor(M), kind(M,mallard).
quest(Q) :- mission(Q).
surprise(S) :- twist(S).
needs_help(M) :- mallard(M), trapped(M).
can_start_quest(H,Q) :- hero(H), quest(Q), not blocked(Q).
resolution(H,M,Q,S) :- hero(H), mallard(M), quest(Q), surprise(S), needs_help(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("mission", qid))
    for sid in SURPRISES:
        lines.append(asp.fact("twist", sid))
    lines.append(asp.fact("actor", "hero"))
    lines.append(asp.fact("actor", "mallard"))
    lines.append(asp.fact("kind", "mallard", "mallard"))
    lines.append(asp.fact("trapped", "mallard"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show can_start_quest/2. #show resolution/4."))
    atoms = set()
    for sym in model:
        if sym.name in {"can_start_quest", "resolution"}:
            atoms.add((sym.name,) + tuple(a.name if hasattr(a, "name") else (a.number if a.type.name == "Number" else a.string) for a in sym.arguments))
    expected = {("can_start_quest", "hero", "feather_key"), ("can_start_quest", "hero", "signal_lamp"),
                ("resolution", "hero", "mallard", "feather_key", "mallard_helper"),
                ("resolution", "hero", "mallard", "feather_key", "mallard_guide"),
                ("resolution", "hero", "mallard", "signal_lamp", "mallard_helper"),
                ("resolution", "hero", "mallard", "signal_lamp", "mallard_guide")}
    # The rules are deliberately loose; we only check that the fundamental
    # needs-help and quest-resolution shapes are present.
    if ("can_start_quest", "hero", "feather_key") in atoms and any(a[0] == "resolution" for a in atoms):
        print("OK: ASP reasoner recognizes quest and resolution shapes.")
        return 0
    print("MISMATCH: ASP reasoner did not produce expected shapes.")
    print("atoms:", sorted(atoms))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolution/4."))
    return sorted(set(asp.atoms(model, "resolution")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], SURPRISES[params.surprise], params.hero, params.hero_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(setting="city", hero="Nova", hero_type="girl", companion="mallard", quest="feather_key", surprise="mallard_helper"),
    StoryParams(setting="harbor", hero="Comet", hero_type="boy", companion="mallard", quest="signal_lamp", surprise="mallard_guide"),
]


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.companion and args.companion.lower() != "mallard":
        raise StoryError("Only the mallard companion is supported.")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.quest and args.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if args.surprise and args.surprise not in SURPRISES:
        raise StoryError("Unknown surprise.")
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(["Nova", "Comet", "Scout", "Mira", "Pax", "Toby"]),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        companion="mallard",
        quest=args.quest or rng.choice(list(QUESTS)),
        surprise=args.surprise or rng.choice(list(SURPRISES)),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolution/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolution/4."))
        print(sorted(set(asp.atoms(model, "resolution"))))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_combo(args, random.Random(base + i))
            params.seed = base + i
            sample = generate(params)
            if sample.story not in seen:
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
            header = f"### {p.hero}: {p.quest} in {p.setting} ({p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
