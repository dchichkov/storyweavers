#!/usr/bin/env python3
"""
storyworlds/worlds/telegram_quest_nursery_rhyme.py
==================================================

A small story world for a nursery-rhyme-style quest about a telegram:
someone must carry a message, face a little obstacle, and finish with a
bright, child-friendly ending image.

The generated stories are built from state changes in a tiny world model:
a messenger travels with a telegram, the path may be blocked, help may be
needed, and the delivery changes who feels worried or glad.
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
    carrier: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "maid"}
        male = {"boy", "father", "man", "king", "knight"}
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
    afford_paths: set[str] = field(default_factory=set)
    obstacles: set[str] = field(default_factory=set)


@dataclass
class Path:
    id: str
    verb: str
    gerund: str
    rush: str
    obstacle: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    holder: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    offer: str
    fix: str
    helps_against: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.path: str = ""
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.path = self.path
        return clone


@dataclass
class StoryParams:
    place: str
    path: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "lane": Setting(place="the little lane", afford_paths={"bridge", "rainbow", "hill"}),
    "wood": Setting(place="the whispering wood", afford_paths={"bridge", "hill"}),
    "village": Setting(place="the sleepy village", afford_paths={"bridge", "rainbow"}),
}

PATHS = {
    "bridge": Path(
        id="bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        rush="dash to the bridge",
        obstacle="a wobble in the boards",
        risk="the telegram could slip into the stream",
        keyword="bridge",
        tags={"bridge", "water"},
    ),
    "hill": Path(
        id="hill",
        verb="climb the hill",
        gerund="climbing the hill",
        rush="run up the hill",
        obstacle="a windy steep patch",
        risk="the telegram could flutter away",
        keyword="hill",
        tags={"hill", "wind"},
    ),
    "rainbow": Path(
        id="rainbow",
        verb="follow the rainbow",
        gerund="following the rainbow",
        rush="hurry toward the rainbow",
        obstacle="a cloudburst of spray",
        risk="the telegram could get damp",
        keyword="rainbow",
        tags={"rainbow", "rain"},
    ),
}

PRIZES = {
    "telegram": Prize(
        label="telegram",
        phrase="a folded telegram with a blue seal",
        type="telegram",
        holder="hand",
    ),
}

HELPERS = {
    "kite": Helper(
        id="kite",
        label="a bright kite",
        offer="tie the telegram to the string",
        fix="the kite can tug the message safely over the wind",
        helps_against={"wind"},
    ),
    "boot": Helper(
        id="boot",
        label="red rain boots",
        offer="wear the red rain boots",
        fix="the boots keep little steps steady through the wet",
        helps_against={"rain", "water"},
    ),
    "cart": Helper(
        id="cart",
        label="a tiny handcart",
        offer="roll the telegram in a tiny handcart",
        fix="the cart keeps the message from slipping",
        helps_against={"water", "wind", "hill"},
    ),
}

NAMES = {
    "girl": ["Mabel", "Nina", "Poppy", "Ruby", "Tilly"],
    "boy": ["Benny", "Clive", "Denny", "Jasper", "Rory"],
}

TRAITS = ["brave", "gentle", "small", "cheery", "spry"]


def path_at_risk(path: Path, prize: Prize) -> bool:
    return True if prize.label == "telegram" else False


def select_helper(path: Path) -> Optional[Helper]:
    for helper in HELPERS.values():
        if path.tags & helper.helps_against:
            return helper
    return None


def explain_rejection(path: Path) -> str:
    return (
        f"(No story: the path {path.keyword} has no reasonable helper in this tiny world.)"
    )


class Rule:
    def __init__(self, name: str, fn):
        self.name = name
        self.fn = fn


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    messenger = next((e for e in world.characters() if e.meters.get("travel", 0) >= THRESHOLD), None)
    if not messenger:
        return out
    if world.facts.get("trouble_seen"):
        return out
    world.facts["trouble_seen"] = True
    out.append("The path gave a little wobble and the messenger paused.")
    return out


CAUSAL_RULES = [Rule("trouble", _r_trouble)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, path: Path, prize_cfg: Prize, hero_name: str, hero_type: str, helper_key: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"travel": 0.0}, memes={"hope": 0.0}))
    sender = world.add(Entity(id="sender", kind="character", type="mother", label="the sender", memes={"worry": 1.0}))
    prize = world.add(Entity(id="telegram", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=sender.id, carrier=hero.id))
    helper = HELPERS[helper_key]

    world.say(f"{hero.id} was a little {next(t for t in [hero_type, 'child'] if t)} who loved a quest by day.")
    world.say(f"{hero.pronoun().capitalize()} was chosen to carry {prize.phrase} across {world.setting.place}.")
    world.say(f"The message was important, and {sender.label} worried until it reached the right door.")

    world.para()
    world.say(f"One bright morning, {hero.id} set off to {path.verb}.")
    hero.meters["travel"] += 1
    world.path = path.id
    if path.keyword == "rainbow":
        world.say("The rainbow shone like a ribbon in the sky.")
    elif path.keyword == "bridge":
        world.say("The bridge creaked softly over the little water below.")
    else:
        world.say("The hill rose up like a sleepy green hump.")
    world.say(f"Then came {path.obstacle}, and {path.risk}.")

    propagate(world, narrate=True)

    world.para()
    world.say(f"{hero.id} held the telegram tight and looked around for help.")
    world.say(f"Kindly, {helper.label} came along and said they could {helper.offer}.")
    world.say(f"That was the clever way, because {helper.fix}.")

    hero.memes["hope"] += 1
    world.facts["helper"] = helper
    world.facts["hero"] = hero
    world.facts["sender"] = sender
    world.facts["prize"] = prize
    world.facts["path"] = path

    world.para()
    world.say(f"So {hero.id} went on, small feet pattering in tune.")
    if path.keyword == "hill":
        world.say(f"{hero.id} climbed straight on, and the little cart helped the telegram stay snug.")
    elif path.keyword == "bridge":
        world.say(f"{hero.id} crossed safely, and the bright kite kept the message steady in the breeze.")
    else:
        world.say(f"{hero.id} went on, and the red boots kept the steps dry enough to keep going.")
    sender.memes["worry"] = 0.0
    sender.memes["glad"] = 1.0
    world.say(f"At last, the telegram reached the door, and {sender.label} was glad as could be.")
    world.say(f"{hero.id} smiled at the end of the quest, with the little message delivered neat and neat.")

    world.facts.update(
        hero=hero,
        sender=sender,
        prize=prize,
        helper=helper,
        path=path,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme-style quest story that includes the word "telegram".',
        f"Tell a gentle story where {f['hero'].id} carries a telegram across {f['setting'].place} and meets a small problem.",
        f"Write a rhyming-feeling children's story about a telegram, a helper, and a happy delivery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sender: Entity = f["sender"]
    prize: Entity = f["prize"]
    helper: Helper = f["helper"]
    path: Path = f["path"]
    return [
        QAItem(
            question=f"Who carried the telegram in the story?",
            answer=f"{hero.id} carried the telegram as the little messenger on the quest.",
        ),
        QAItem(
            question=f"What was the important message?",
            answer=f"It was a telegram, a folded message that had to reach the right door.",
        ),
        QAItem(
            question=f"Who was worried until the telegram arrived?",
            answer=f"{sender.label} was worried until the telegram arrived safely.",
        ),
        QAItem(
            question=f"What helped make the path safer?",
            answer=f"{helper.label} helped by offering a clever way to carry the telegram on {path.keyword}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a telegram?",
            answer="A telegram is a short message sent quickly to tell someone important news.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey where someone tries hard to reach a goal or deliver something important.",
        ),
        QAItem(
            question="Why does a helper matter in a quest?",
            answer="A helper can make a hard job easier and safer, so the traveler can keep going.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
        if e.carrier:
            bits.append(f"carrier={e.carrier}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  path: {world.path}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lane", path="bridge", prize="telegram", name="Mabel", gender="girl", helper="cart"),
    StoryParams(place="wood", path="hill", prize="telegram", name="Rory", gender="boy", helper="kite"),
    StoryParams(place="village", path="rainbow", prize="telegram", name="Tilly", gender="girl", helper="boot"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    path_id = args.path or rng.choice(list(PATHS))
    if path_id not in SETTINGS[place].afford_paths:
        raise StoryError(explain_rejection(PATHS[path_id]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, path=path_id, prize="telegram", name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PATHS[params.path], PRIZES[params.prize], params.name, params.gender, params.helper)
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


ASP_RULES = r"""
place(lane). place(wood). place(village).
path(bridge). path(hill). path(rainbow).
affords(lane,bridge). affords(lane,hill). affords(lane,rainbow).
affords(wood,bridge). affords(wood,hill).
affords(village,bridge). affords(village,rainbow).

telegram(telegram).

% A path is valid for the telegram quest when the setting affords it.
valid(Place,Path) :- affords(Place,Path).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for path in sorted(setting.afford_paths):
            lines.append(asp.fact("affords", place, path))
    for path in PATHS:
        lines.append(asp.fact("path", path))
    lines.append(asp.fact("telegram", "telegram"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((place, path) for place, s in SETTINGS.items() for path in s.afford_paths)
    clingo = asp_valid()
    if py == clingo:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" python:", py)
    print(" clingo :", clingo)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme quest storyworld about a telegram.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid quest combos:")
        for place, path in vals:
            print(f"  {place:8} {path}")
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
            header = f"### {p.name}: {p.path} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
