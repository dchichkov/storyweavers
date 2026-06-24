#!/usr/bin/env python3
"""
Standalone storyworld: crypt / passenger / tickle.

A small, child-facing story domain with a rhyming cadence:
a passenger visits a crypt, a tickle causes a twist, and friendship solves
the mystery in a gentle ending.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "king", "prince"}
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    mood: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Companion:
    id: str
    label: str
    help_line: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def gate_ok(setting: Setting, activity: Activity, prize: Prize, companion: Companion) -> bool:
    return (
        activity.id in setting.affords
        and prize.region in {"feet", "torso"}
        and ("friendship" in companion.tags or "mystery" in companion.tags)
    )


SETTINGS = {
    "crypt_hall": Setting("the crypt hall", "stone-cool", affords={"tickle", "twist"}),
    "moon_crypt": Setting("the moonlit crypt", "silver-quiet", affords={"tickle", "twist"}),
    "catacomb_path": Setting("the catacomb path", "echo-bright", affords={"tickle", "twist"}),
}

ACTIVITIES = {
    "tickle": Activity(
        id="tickle",
        verb="tickle the lantern rope",
        gerund="tickling the lantern rope",
        rush="reach for the rope",
        mess="jingle",
        mood="giggly",
        keyword="tickle",
        tags={"tickle", "mystery"},
    ),
    "twist": Activity(
        id="twist",
        verb="twist the old key",
        gerund="twisting the old key",
        rush="turn the key",
        mess="turn",
        mood="curious",
        keyword="twist",
        tags={"twist", "mystery"},
    ),
}

PRIZES = {
    "cloak": Prize("cloak", "a small blue cloak", "cloak", "torso"),
    "boots": Prize("boots", "soft little boots", "boots", "feet"),
}

COMPANIONS = {
    "friend": Companion(
        id="friend",
        label="a gentle friend",
        help_line="A friend can help when a worry grows thick.",
        reveal_line="Friendship can light a puzzly night.",
        tags={"friendship"},
    ),
    "guide": Companion(
        id="guide",
        label="a quiet guide",
        help_line="A guide can point to what is true.",
        reveal_line="A mystery can fade when friends look through.",
        tags={"mystery", "friendship"},
    ),
}

NAMES = ["Mina", "Jo", "Nico", "Ivy", "Rae", "Luca", "Toby", "Zuri"]
TRAITS = ["brave", "bright", "curious", "gentle", "bouncy"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    companion: str
    name: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("crypt_hall", "tickle", "cloak", "friend", "Mina", "curious"),
    StoryParams("moon_crypt", "twist", "boots", "guide", "Luca", "gentle"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for cid, c in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("helps", cid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,A,P,C) :- setting(S), activity(A), prize(P), companion(C),
                        affords(S,A), region(P,R), (R = feet; R = torso),
                        helps(C, friendship).
valid_story(S,A,P,C) :- setting(S), activity(A), prize(P), companion(C),
                        affords(S,A), tag(A, mystery), helps(C, mystery).
#show valid_story/4.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, a, p, c) for s in SETTINGS for a in ACTIVITIES for p in PRIZES for c in COMPANIONS if gate_ok(SETTINGS[s], ACTIVITIES[a], PRIZES[p], COMPANIONS[c])}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming crypt storyworld about a passenger, a tickle, and a mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for p in PRIZES:
                for c in COMPANIONS:
                    if gate_ok(SETTINGS[s], ACTIVITIES[a], PRIZES[p], COMPANIONS[c]):
                        if args.place and s != args.place: continue
                        if args.activity and a != args.activity: continue
                        if args.prize and p != args.prize: continue
                        if args.companion and c != args.companion: continue
                        combos.append((s, a, p, c))
    if not combos:
        raise StoryError("No valid story matches those choices.")
    s, a, p, c = rng.choice(sorted(combos))
    return StoryParams(
        place=s,
        activity=a,
        prize=p,
        companion=c,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def story_lines(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    activity = f["activity"]
    prize = f["prize"]
    world.say(f"In {world.setting.place}, {hero.id} was a {hero.memes.get('trait', 'bright')} passenger with a curious grin.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, for every echo felt like a song in a spin.")
    world.say(f"{hero.id} wore {prize.phrase}, as neat as could be, and rode through the crypt with a soft, careful din.")
    world.para()
    world.say(f"Then {hero.id} saw a clue by a stone-carved gate, and the air turned to wondering, round and thin.")
    world.say(f"{hero.id} wanted to {activity.verb}, but a hidden old puzzle said, 'Wait, look within.'")
    world.say(f"The tickle of doubt made {hero.pronoun('object')} giggle and twist, and the mystery started to begin.")
    world.para()
    world.say(f"At last {comp.label} came close with a kind little smile and a lantern held chin-high and clean.")
    world.say(comp.help_line)
    world.say(f"Together they solved the small mystery: the clue was a note from a lost little friend.")
    world.say(f"{comp.reveal_line}")
    world.say(f"So {hero.id} left hand in hand, and the crypt felt less spooky, more cozy than grim.")
    world.say(f"The passenger found friendship, and the twist in the tale became bright at the end.")


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Luca", "Toby"} else "girl"))
    hero.memes["trait"] = params.trait
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    comp = COMPANIONS[params.companion]
    world.facts.update(hero=hero, prize=prize, companion=comp, activity=ACTIVITIES[params.activity], params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story_lines(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a rhyming story about a passenger in {world.setting.place} who feels a tickle of mystery.",
            f"Tell a gentle tale where {params.name} meets {COMPANIONS[params.companion].label} and solves a small puzzle.",
            f"Create a child-friendly crypt story with friendship, a twist, and a happy ending.",
        ],
        story_qa=[
            QAItem(
                question=f"Who was the passenger in the story?",
                answer=f"The passenger was {params.name}, who went through {world.setting.place} with a curious heart.",
            ),
            QAItem(
                question=f"What made the story twist and start the puzzle?",
                answer=f"The tickle of doubt and the old clue made the story twist into a mystery to solve.",
            ),
            QAItem(
                question=f"How was the mystery solved?",
                answer=f"{COMPANIONS[params.companion].label.capitalize()} helped {params.name} look carefully, and they found that the clue was a note from a lost friend.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a crypt?",
                answer="A crypt is an old underground room or chamber, often built of stone and sometimes used for burials.",
            ),
            QAItem(
                question="What does friendship mean?",
                answer="Friendship means people care about each other, help each other, and stay kind together.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
