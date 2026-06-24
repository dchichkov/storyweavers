#!/usr/bin/env python3
"""
A small storyworld for a campground rhyming misunderstanding.

The seed tale idea:
A child at a campground hears a silly rhyme about a "kamikaze" kite and
misunderstands it as a dangerous dare. That confusion makes the child do a
stupid, over-hasty thing. A grown-up notices the misunderstanding, explains the
rhyme, and helps the child turn the scene into a safe campfire rhyme instead.

This world keeps the state tiny and concrete:
- physical meters: distance, mess, fire_safety, tear, calm
- emotional memes: confusion, fear, pride, relief, trust

The story is generated from simulated state, not from a frozen template.
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
# Core world model
# ---------------------------------------------------------------------------

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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the campground"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    mess: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "campground": Setting(place="the campground", affords={"rhyme"}),
}

ACTIVITIES = {
    "rhyme": Activity(
        id="rhyme",
        verb="join the rhyme",
        gerund="rhyming by the fire",
        rush="rush toward the fire ring",
        keyword="rhyme",
        mess="confusion",
        zone="campfire",
        tags={"rhyme", "misunderstanding"},
    ),
}

PRIZES = {
    "songbook": Prize(
        id="songbook",
        label="songbook",
        phrase="a little songbook with bouncy lines",
        region="hands",
    ),
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a bright camping lantern",
        region="hands",
    ),
}


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "campground"
    activity: str = "rhyme"
    prize: str = "songbook"
    name: str = "Nina"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------

def _say_intro(world: World, hero: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} was a little {hero.pronoun('subject')} who loved the campground, "
        f"where the pines went whispering and the kettles went clinking."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} liked {activity.gerund}, especially when a grown-up "
        f"read from {prize.phrase} by the fire."
    )
    world.say(
        f"{helper.pronoun('possessive').capitalize()} {helper.noun()} had brought the {prize.label} so the words could bounce and sing."
    )


def _predict_misunderstanding(world: World, hero: Entity, activity: Activity) -> bool:
    sim = world.copy()
    sim.facts["heard_word"] = activity.keyword
    sim.facts["confusion"] = 1.0
    return True


def _misunderstand(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["confusion"] = 1.0
    hero.memes["fear"] = 1.0
    world.say(
        f"Then someone in the circle said the word \"kamikaze\" in a silly rhyme, and {hero.id} froze."
    )
    world.say(
        f"{hero.id} thought it meant a dangerous dare, not a funny rhyme word."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} made a stupid, hasty move and dashed too close to the fire ring."
    )
    world.facts["misunderstanding"] = True


def _rule_stumble(world: World, hero: Entity, prize: Entity) -> list[str]:
    out: list[str] = []
    if hero.memes.get("confusion", 0.0) < THRESHOLD:
        return out
    if hero.meters.get("stumble", 0.0) >= THRESHOLD:
        return out
    hero.meters["stumble"] = 1.0
    hero.meters["distance_from_fire"] = 0.5
    hero.meters["mess"] = 1.0
    out.append(f"{hero.id} stumbled in a silly hurry.")
    if prize.id == "songbook":
        prize.meters["bent_corner"] = 1.0
        out.append(f"The songbook got a bent corner.")
    return out


def _rule_calm(world: World, hero: Entity, helper: Entity) -> list[str]:
    out: list[str] = []
    if hero.memes.get("confusion", 0.0) < THRESHOLD:
        return out
    if helper.memes.get("trust", 0.0) >= THRESHOLD:
        return out
    helper.memes["trust"] = 1.0
    hero.memes["confusion"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] = 1.0
    hero.memes["pride"] = 1.0
    out.append(f"{helper.id} knelt down and explained the rhyme word.")
    out.append(f"{hero.id} listened, and the worry washed away.")
    return out


def _rule_song(world: World, hero: Entity, helper: Entity, prize: Entity) -> list[str]:
    out: list[str] = []
    if hero.memes.get("relief", 0.0) < THRESHOLD:
        return out
    if world.facts.get("song_done"):
        return out
    world.facts["song_done"] = True
    out.append(f"Together they turned the mistake into a safer campfire rhyme.")
    out.append(f"{hero.id} sat back down with the {prize.label}, smiling and sing-songing the new line.")
    return out


def propagate(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_rule_stumble, _rule_calm, _rule_song):
            lines = rule(world, hero, helper) if rule is _rule_calm else rule(world, hero, prize) if rule is _rule_stumble else rule(world, hero, helper, prize)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         name: str = "Nina", gender: str = "girl", parent: str = "mother",
         trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    helper = world.add(Entity(id=parent.title(), kind="character", type=parent, label=parent))
    prize = world.add(Entity(id=prize_cfg.id, type="thing", label=prize_cfg.label,
                             phrase=prize_cfg.phrase, caretaker=helper.id, owner=hero.id))

    _say_intro(world, hero, helper, prize, activity)
    world.para()
    world.say(
        f"At the campground, {hero.id} leaned in to hear the fire-side rhyme."
    )
    world.say(
        f"A line with the word \"kamikaze\" popped out, and {hero.id} misunderstood it at once."
    )
    _misunderstand(world, hero, helper, activity, prize)
    propagate(world, hero, helper, prize)
    world.para()
    if world.facts.get("song_done"):
        world.say(
            f"By the end, the campsite was quiet again, except for a bright little rhyme that made everyone grin."
        )
    else:
        world.say(
            f"By the end, the misunderstanding had faded, and the campground felt warm and safe again."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=activity,
        setting=setting,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a rhyming story about a child at a campground who hears the word "kamikaze" and gets it wrong.',
        f"Tell a gentle story where {hero.id} makes a stupid hasty choice because of a misunderstanding, then a grown-up fixes it.",
        "Write a tiny campsite story with a rhyme, a mistake, and a safer ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Where did {hero.id} hear the rhyme?",
            answer=f"{hero.id} heard it at the campground by the fire ring.",
        ),
        QAItem(
            question=f"What word did {hero.id} misunderstand?",
            answer='The confusing word was "kamikaze". {hero.id} thought it meant a dangerous dare, but it was just part of a rhyme.'.replace("{hero.id}", hero.id),
        ),
        QAItem(
            question=f"What did {helper.id} do to help?",
            answer=f"{helper.id} knelt down, explained the rhyme word, and helped turn the mistake into a safer song.",
        ),
        QAItem(
            question=f"What happened to the {prize.label}?",
            answer=f"The {prize.label} got a bent corner during the hasty move, but the story ended with everyone calm and singing safely.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks the wrong thing and reacts before the truth is clear.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a playful sound pattern where words end with matching or similar sounds, like in a song or poem.",
        ),
        QAItem(
            question="What is a campground?",
            answer="A campground is a place where people set up tents, share meals, and enjoy being outdoors.",
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
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
misunderstanding(H) :- hears(H, kamikaze), not knows(H, kamikaze).
stupid_move(H) :- misunderstanding(H), rushes(H).
calmed(H) :- explained(H), misunderstanding(H).
safe_end(H) :- calmed(H), rhymes(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("label", pid, p.label))
    lines.append(asp.fact("hears", "hero", "kamikaze"))
    lines.append(asp.fact("rushes", "hero"))
    lines.append(asp.fact("explained", "hero"))
    lines.append(asp.fact("rhymes", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/1. #show stupid_move/1. #show calmed/1. #show safe_end/1."))
    atoms = set((sym.name, tuple((a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name) for a in sym.arguments)) for sym in model)
    expected = {
        ("misunderstanding", ("hero",)),
        ("stupid_move", ("hero",)),
        ("calmed", ("hero",)),
        ("safe_end", ("hero",)),
    }
    return atoms == expected


def asp_verify() -> int:
    ok = asp_valid()
    if ok:
        print("OK: ASP twin is coherent.")
        return 0
    print("MISMATCH: ASP twin failed parity check.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming campground storyworld with a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait")
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
    place = args.place or "campground"
    activity = args.activity or "rhyme"
    prize = args.prize or "songbook"
    if place not in SETTINGS:
        raise StoryError("This story only supports the campground setting.")
    if activity not in ACTIVITIES:
        raise StoryError("This story only supports the rhyme activity.")
    if prize not in PRIZES:
        raise StoryError("Unknown prize.")
    gender = args.gender or "girl"
    name = args.name or rng.choice(["Nina", "Maya", "Eli", "Toby"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(["curious", "playful", "bouncy", "silly"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


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
        print(asp_program("#show misunderstanding/1. #show stupid_move/1. #show calmed/1. #show safe_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.seed is None:
        base_seed = random.randrange(2**31)
    else:
        base_seed = args.seed

    if args.asp:
        import asp
        print(asp_program("#show misunderstanding/1. #show stupid_move/1. #show calmed/1. #show safe_end/1."))
        return

    samples: list[StorySample] = []
    if args.all:
        params = StoryParams()
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
            if len(samples) >= args.n:
                break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
