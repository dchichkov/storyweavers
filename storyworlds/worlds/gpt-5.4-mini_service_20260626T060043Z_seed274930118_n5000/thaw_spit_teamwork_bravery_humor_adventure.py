#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thaw_spit_teamwork_bravery_humor_adventure.py
============================================================================================================

A small adventure storyworld about a frosty route, a stubborn freeze, and a
team that finds a brave, funny way to get moving again.

Premise:
- A child hero and a helper are traveling on a winter adventure.
- The path, gate, bridge, or cave entrance is frozen shut.
- The group needs teamwork to thaw the blockage.
- The world also includes "spit" as a concrete action: the ice can spit
  cold spray, the wind can spit sleet, or a goblin-like rock spitter can
  spray slush, making the journey trickier.

Story shape:
- Setup: the team sets out for a goal.
- Tension: the frozen obstacle blocks the route and spits cold water/sleet.
- Turn: brave, coordinated action thaws the blockage.
- Resolution: the route opens, the group laughs, and the adventure continues.

The file is self-contained and uses only the standard library at import time.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["cold", "wet", "blocked", "thawed", "sprayed", "travel", "distance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "bravery", "humor", "teamwork", "alarm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    obstacle: str
    spit: str
    goal: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    prep: str
    use: str
    covers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.challenge: Optional[Challenge] = None
        self.aid: Optional[Aid] = None
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.challenge = self.challenge
        clone.aid = self.aid
        return clone


@dataclass
class StoryParams:
    place: str
    challenge: str
    aid: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


SETTINGS = {
    "bridge": Setting(place="the frozen bridge", kind="outdoor", affords={"cross"}),
    "cave": Setting(place="the ice cave", kind="outdoor", affords={"enter"}),
    "trail": Setting(place="the mountain trail", kind="outdoor", affords={"hike"}),
    "harbor": Setting(place="the little harbor", kind="outdoor", affords={"sail"}),
}

CHALLENGES = {
    "ice_gate": Challenge(
        id="ice_gate",
        verb="open the ice gate",
        gerund="opening the ice gate",
        obstacle="ice",
        spit="spits cold spray",
        goal="reach the hidden map room",
        sound="crack",
        tags={"thaw", "spit", "adventure"},
    ),
    "frozen_bridge": Challenge(
        id="frozen_bridge",
        verb="cross the frozen bridge",
        gerund="crossing the frozen bridge",
        obstacle="frost",
        spit="spits sleet",
        goal="get to the far hill",
        sound="creak",
        tags={"thaw", "spit", "adventure"},
    ),
    "locked_cave": Challenge(
        id="locked_cave",
        verb="unlock the cave door",
        gerund="unlocking the cave door",
        obstacle="ice",
        spit="spits icy drips",
        goal="find the lantern treasure",
        sound="clink",
        tags={"thaw", "spit", "adventure"},
    ),
}

AIDS = {
    "hot_tea": Aid(
        id="hot_tea",
        label="a thermos of hot tea",
        phrase="a warm thermos of tea",
        prep="pour hot tea along the frozen edge",
        use="keeps hands warm and helps the ice thaw",
        covers={"ice", "frost"},
        tags={"thaw", "teamwork"},
    ),
    "blanket": Aid(
        id="blanket",
        label="a wool blanket",
        phrase="a thick wool blanket",
        prep="wrap the stubborn lock in a wool blanket",
        use="holds warmth close so the freeze loosens",
        covers={"ice", "frost"},
        tags={"thaw", "teamwork"},
    ),
    "torch": Aid(
        id="torch",
        label="a small lantern torch",
        phrase="a tiny lantern torch",
        prep="shine the lantern torch at the cold seam",
        use="gives enough heat to thaw the seam",
        covers={"ice"},
        tags={"thaw", "bravery"},
    ),
    "salty_soup": Aid(
        id="salty_soup",
        label="a bowl of salty soup",
        phrase="a steaming bowl of salty soup",
        prep="tip salty soup where the ice is thickest",
        use="helps melt the frozen edge",
        covers={"ice", "frost"},
        tags={"thaw", "humor"},
    ),
}

HERO_NAMES = ["Mila", "Niko", "Tessa", "Pip", "Jules", "Arlo", "Wren", "Sami"]
SIDEKICK_NAMES = ["Fox", "Bram", "Moss", "Dot", "June", "Kai", "Bean"]
TRAITS = ["curious", "brave", "cheerful", "quick-thinking", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for chal_id in setting.affords:
            for aid_id in AIDS:
                if challenge_can_use_aid(CHALLENGES[chal_id], AIDS[aid_id]):
                    combos.append((place, chal_id, aid_id))
    return combos


def challenge_can_use_aid(challenge: Challenge, aid: Aid) -> bool:
    return bool(challenge.obstacle in aid.covers and "thaw" in aid.tags)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A winter adventure storyworld about thawing a frozen path with teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    if args.challenge and args.aid:
        if not challenge_can_use_aid(CHALLENGES[args.challenge], AIDS[args.aid]):
            raise StoryError("That aid would not reasonably thaw that obstacle.")

    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if True else True]
    combos = [c for c in combos
              if args.challenge is None or c[1] == args.challenge
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("No valid adventure combination matches the given options.")

    place, challenge, aid = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(place=place, challenge=challenge, aid=aid, hero=hero, sidekick=sidekick)


def _setup(world: World, hero: Entity, sidekick: Entity, challenge: Challenge, aid: Aid) -> None:
    world.challenge = challenge
    world.aid = aid
    hero.memes["bravery"] += 1
    hero.memes["joy"] += 1
    sidekick.memes["humor"] += 1
    world.say(f"{hero.id} and {sidekick.id} reached {world.setting.place} on a cold day.")
    world.say(f"They were chasing {challenge.goal}, and {hero.id} carried {aid.phrase}.")
    world.say(f"Together they whispered that this would be an adventure, not a problem.")


def _pressure(world: World, hero: Entity, sidekick: Entity, challenge: Challenge) -> None:
    hero.memes["fear"] += 1
    sidekick.meters["sprayed"] += 1
    world.para()
    world.say(f"Then the {challenge.obstacle} got worse and {challenge.spit} at their boots.")
    world.say(f"The frozen place made a {challenge.sound} sound as it tightened its grip.")
    world.say(f"{hero.id} felt a little scared, but {sidekick.id} cracked a joke to keep the team smiling.")


def _thaw(world: World, hero: Entity, sidekick: Entity, challenge: Challenge, aid: Aid) -> None:
    world.para()
    hero.memes["bravery"] += 1
    hero.memes["teamwork"] += 1
    sidekick.memes["teamwork"] += 1
    world.get(hero.id).meters["travel"] += 1
    world.say(f"{hero.id} took a breath, stood close, and said they could do it together.")
    world.say(f"With real teamwork, they began to {aid.prep}.")
    world.say(f"The warmth {aid.use}, and at last the frozen barrier started to thaw.")
    world.say(f"The ice gave a soft {challenge.sound}, then split open like a door waking up.")


def _finish(world: World, hero: Entity, sidekick: Entity, challenge: Challenge) -> None:
    world.para()
    hero.memes["joy"] += 2
    sidekick.memes["humor"] += 1
    world.say(f"The path opened, and the two friends hurried on toward {challenge.goal}.")
    world.say(f"Behind them, the cold place only had time to spit one last bit of slush.")
    world.say(f"{hero.id} laughed, {sidekick.id} grinned, and the adventure felt bigger than the ice.")


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in {"Mila", "Tessa", "Wren"} else "boy"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="fox" if params.sidekick == "Fox" else "friend"))
    challenge = CHALLENGES[params.challenge]
    aid = AIDS[params.aid]
    _setup(world, hero, sidekick, challenge, aid)
    _pressure(world, hero, sidekick, challenge)
    _thaw(world, hero, sidekick, challenge, aid)
    _finish(world, hero, sidekick, challenge)
    world.facts.update(hero=hero, sidekick=sidekick, challenge=challenge, aid=aid, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story for a child where {f['hero'].id} and {f['sidekick'].id} must thaw a frozen obstacle.",
        f"Tell a brave and funny winter tale in which the team reaches {f['challenge'].goal} after the ice spits slush.",
        f"Create a simple story about teamwork, bravery, and humor at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    challenge = f["challenge"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Why did {hero.id} and {sidekick.id} need teamwork at {world.setting.place}?",
            answer=f"They needed teamwork because the {challenge.obstacle} blocked the route and kept {challenge.spit} at them."
        ),
        QAItem(
            question=f"What did they use to thaw the frozen obstacle?",
            answer=f"They used {aid.phrase}, which gave enough warmth to thaw the frozen barrier."
        ),
        QAItem(
            question=f"How did the story end after the ice broke open?",
            answer=f"It ended with the path open, the team laughing, and {hero.id} and {sidekick.id} heading toward {challenge.goal}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does thaw mean?",
            answer="To thaw means to become warm enough for ice or frozen water to melt."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together toward the same goal."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when you feel nervous."
        ),
        QAItem(
            question="Why can humor help on an adventure?",
            answer="Humor can help because a funny moment can cheer people up and make a hard task feel easier."
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
can_use(P,C,A) :- affords(P,C), aid(A), challenge(C), thaw_aid(A), obstacle(C,O), covers(A,O).
valid(P,C,A) :- can_use(P,C,A).
"""


def asp_facts() -> str:
    import asp
    out = []
    for p, s in SETTINGS.items():
        out.append(asp.fact("setting", p))
        out.append(asp.fact("kind", p, s.kind))
        for c in s.affords:
            out.append(asp.fact("affords", p, c))
    for cid, c in CHALLENGES.items():
        out.append(asp.fact("challenge", cid))
        out.append(asp.fact("obstacle", cid, c.obstacle))
        out.append(asp.fact("spits", cid, c.spit))
    for aid, a in AIDS.items():
        out.append(asp.fact("aid", aid))
        out.append(asp.fact("thaw_aid", aid))
        for c in a.covers:
            out.append(asp.fact("covers", aid, c))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in clingo:", sorted(cl - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    story_world = tell(world, params)
    return StorySample(
        params=params,
        story=story_world.render(),
        prompts=generation_prompts(story_world),
        story_qa=story_qa(story_world),
        world_qa=world_knowledge_qa(story_world),
        world=story_world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
    StoryParams(place="bridge", challenge="frozen_bridge", aid="hot_tea", hero="Mila", sidekick="Fox"),
    StoryParams(place="cave", challenge="locked_cave", aid="blanket", hero="Tessa", sidekick="Bram"),
    StoryParams(place="trail", challenge="ice_gate", aid="torch", hero="Arlo", sidekick="Bean"),
    StoryParams(place="harbor", challenge="frozen_bridge", aid="salty_soup", hero="Wren", sidekick="Kai"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.aid:
        if not challenge_can_use_aid(CHALLENGES[args.challenge], AIDS[args.aid]):
            raise StoryError("That aid cannot reasonably thaw that challenge.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("No valid adventure combination matches those options.")
    place, challenge, aid = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(place=place, challenge=challenge, aid=aid, hero=hero, sidekick=sidekick)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid adventure combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
