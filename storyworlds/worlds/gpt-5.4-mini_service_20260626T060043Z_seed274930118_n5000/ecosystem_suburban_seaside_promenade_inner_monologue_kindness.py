#!/usr/bin/env python3
"""
storyworlds/worlds/ecosystem_suburban_seaside_promenade_inner_monologue_kindness.py
===================================================================================

A small, standalone story world for a pirate-flavored seaside promenade tale
with inner monologue, kindness, and friendship.

The seed idea:
- A child on a seaside promenade notices a tiny part of the local ecosystem in
  trouble.
- The child first thinks to keep going, then listens to their inner monologue,
  chooses kindness, and asks a friend to help.
- Together they fix the problem and end the day with a warmer friendship and a
  cleaner promenade.

This world keeps the prose child-facing, concrete, and state-driven: the world
model tracks what is seen, what is worried about, what is helped, and how the
friendship changes.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the seaside promenade"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    thought: str
    action: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_litter(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("litter", 0.0) < THRESHOLD:
            continue
        for ent in world.entities.values():
            if ent.type != "ecosystem" or ent.label not in {"crab", "gull", "seagrass"}:
                continue
            if ent.meters.get("troubled", 0.0) < THRESHOLD:
                continue
            sig = ("litter", actor.id, ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"The little trouble on the promenade made the sea life uneasy.")
    return out


CAUSAL_RULES = [_r_litter]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for rule in CAUSAL_RULES:
        s = rule(world)
        produced.extend(s)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def inner_monologue(hero: Entity, concern: str) -> str:
    return (
        f"{hero.pronoun().capitalize()} thought, \"If I just walk past, "
        f"that little thing might stay stuck. But if I help, the day can be kinder.\""
    )


def setting_detail(setting: Setting) -> str:
    return (
        "The seaside promenade had bright shop windows, low railings, and salt air "
        "that drifted over the benches."
    )


def predict_help(world: World, hero: Entity, activity: Activity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["kindness"] = sim.get(hero.id).memes.get("kindness", 0.0) + 1
    sim.get(hero.id).meters[activity.mess] = sim.get(hero.id).meters.get(activity.mess, 0.0) + 1
    return {"helped": True, "friendship": sim.get(hero.id).memes.get("friendship", 0.0)}


def act_1(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little pirate with a brave hat and a curious eye."
    )
    world.say(
        f"{hero.id} liked {activity.gerund} along {world.setting.place}, "
        f"where the breeze smelled like salt and chips."
    )
    world.say(
        f"One day, {hero.id} had {prize.phrase}, and {friend.id} walked beside {hero.id} like a true matey."
    )


def act_2(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity, aid: Aid) -> None:
    world.para()
    world.say(setting_detail(world.setting))
    world.say(
        f"Then {hero.id} noticed a tiny crab near the rail, caught under a bit of string."
    )
    world.say(
        inner_monologue(hero, "the crab looked scared")
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.meters["litter"] = hero.meters.get("litter", 0.0) + 1
    world.say(
        f"{hero.id} did not keep striding on. {hero.pronoun().capitalize()} chose kindness and knelt down."
    )
    world.say(
        f"\"Friend, can ye hold the prize while I free the poor little crab?\" {hero.id} asked."
    )
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    world.say(
        f"{friend.id} grinned and held {prize.phrase} steady. \"Aye, matey,\" said {friend.id}, "
        f"\"we'll help together.\""
    )
    world.say(
        f"With {aid.label}, {hero.id} lifted the string away and set the crab free."
    )
    propagate(world, narrate=True)


def act_3(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity, aid: Aid) -> None:
    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(
        f"The crab skittered safely back to the rocks, and the tide kept its gentle song."
    )
    world.say(
        f"{hero.id} smiled so wide it almost hid the brim of the pirate hat."
    )
    world.say(
        f"{friend.id} and {hero.id} shared a happy look, and the promenade felt cleaner and kinder."
    )
    world.say(
        f"After that, {hero.id} and {friend.id} kept walking together, {activity.gerund}, "
        f"with {prize.phrase} safe and their friendship stronger than before."
    )


SETTINGS = {
    "promenade": Setting(
        place="the seaside promenade",
        affords={"stroll", "tidewatch"},
    )
}

ACTIVITIES = {
    "tidewatch": Activity(
        id="tidewatch",
        verb="watch the tide",
        gerund="watching the tide",
        thought="the tide was hiding little treasures",
        action="help with litter",
        mess="care",
        zone={"shore"},
        keyword="tide",
        tags={"ecosystem", "suburban", "seaside"},
    ),
    "stroll": Activity(
        id="stroll",
        verb="stroll the promenade",
        gerund="strolling by the rail",
        thought="the promenade was full of windy stories",
        action="pause and look",
        mess="care",
        zone={"rail"},
        keyword="promenade",
        tags={"suburban", "seaside"},
    ),
}

PRIZES = {
    "shell": Prize(
        label="shell charm",
        phrase="a bright shell charm on a cord",
        type="charm",
        region="torso",
    )
}

AIDS = {
    "tweezers": Aid(
        id="tweezers",
        label="a pair of tiny tweezers",
        prep="use a pair of tiny tweezers",
        tail="kept the crab safe",
        guards={"string"},
        covers={"hands"},
    )
}

HERO_NAMES = ["Nell", "Milo", "Jory", "Tessa", "Pip", "Rory"]
FRIEND_NAMES = ["Finn", "Mara", "Bea", "Otis", "Lumi", "Sailor"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested options do not fit this promenade tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Seaside promenade pirate tale world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.place or args.activity or args.prize:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.activity is None or c[1] == args.activity)
            and (args.prize is None or c[2] == args.prize)
        ]
    if not combos:
        raise StoryError(explain_rejection())
    place, activity, prize = rng.choice(combos)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        hero_name=args.name or rng.choice(HERO_NAMES),
        friend_name=args.friend or rng.choice(FRIEND_NAMES),
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label="pirate kid"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", label="matey friend"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    crab = world.add(Entity(id="crab", type="ecosystem", label="crab"))
    crab.meters["troubled"] = 1
    aid = AIDS["tweezers"]

    act_1(world, hero, friend, activity, prize)
    act_2(world, hero, friend, activity, prize, aid)
    act_3(world, hero, friend, activity, prize, aid)

    world.facts.update(hero=hero, friend=friend, prize=prize, activity=activity, aid=aid, crab=crab)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    return [
        f"Write a pirate-flavored story set on the seaside promenade where {hero.id} notices a tiny creature and chooses kindness.",
        f"Tell a short story about friendship and an inner thought that helps {hero.id} decide to help {friend.id}.",
        f"Make a gentle tale where {hero.id} and {friend.id} solve a little problem along the promenade.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} decide to do when {hero.id} saw the crab?",
            answer=f"{hero.id} chose kindness and stopped to help the crab instead of walking past.",
        ),
        QAItem(
            question=f"Who helped {hero.id} by holding {prize.phrase} steady?",
            answer=f"{friend.id} helped {hero.id} by holding {prize.phrase} steady while the crab was freed.",
        ),
        QAItem(
            question=f"What was the problem that changed the walk along the promenade?",
            answer="A tiny crab was caught under a bit of string, so the walk turned into a gentle rescue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a seaside promenade?",
            answer="A seaside promenade is a walkway near the water where people can stroll, look at the sea, and enjoy the fresh air.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, care, or be gentle with someone or something.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy being together.",
        ),
        QAItem(
            question="What does an inner monologue do?",
            answer="An inner monologue is the quiet talking a person does inside their own mind when they are thinking.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Act, Prize) :- setting(Place), affords(Place, Act), prize(Prize).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.hero_name, params.friend_name)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} compatible stories")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, act, prize in valid_combos():
            params = StoryParams(place=place, activity=act, prize=prize, hero_name="Nell", friend_name="Finn")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
