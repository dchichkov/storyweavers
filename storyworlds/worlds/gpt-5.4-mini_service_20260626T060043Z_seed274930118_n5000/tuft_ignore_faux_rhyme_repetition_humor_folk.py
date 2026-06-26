#!/usr/bin/env python3
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
class Character:
    id: str
    kind: str = "character"
    role: str = "villager"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "woman", "grandmother", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "man", "grandfather", "boyish"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    faux: bool = False

    def it(self) -> str:
        return "them" if self.label.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str):
        if text:
            self.paragraphs[-1].append(text)

    def para(self):
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def worn_items(self, actor_id: str):
        out = []
        for e in self.entities.values():
            if isinstance(e, Thing) and e.worn_by == actor_id:
                out.append(e)
        return out


def threshold(x: float) -> bool:
    return x >= 1.0


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Character(id=hero_name, role="boy" if hero_name in {"Milo", "Otis", "Jory"} else "girl"))
    helper = world.add(Character(id=helper_name, role="grandmother"))
    prize = world.add(Thing(id="prize", label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region))
    faux = world.add(Thing(id="faux", label="faux token", phrase="a shiny faux token", faux=True))

    hero.memes["joy"] = 1
    helper.memes["warmth"] = 1
    prize.worn_by = hero.id

    world.say(f"Once in {setting.place}, by a hedge and a gate, lived {hero_name}, a small child with a bright heart.")
    world.say(f"{helper_name}, the old grandmother, kept a kindly eye, and often sang, “Soft feet, sweet treat, keep trouble from the street.”")
    world.say(f"{hero_name} loved {activity.rhyme}, and the whole lane knew the tune by heart.")

    world.para()
    world.say(f"One day the {setting.detail} grew busy, and a fox yipped beyond the fence.")
    world.say(f"{hero_name} wanted to {activity.verb}, though {hero_name}'s {helper_name} warned, “Do not {activity.rush}; the {prize_cfg.label} may be spoiled.”")
    world.say(f"But {hero_name} smiled, and chose to ignore the warning, for the prank of play felt too sweet.")

    world.zone = set(activity.zone)
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0) + 1
    if prize.region in activity.zone:
        prize.meters[activity.mess] = prize.meters.get(activity.mess, 0) + 1
        prize.meters["dirty"] = prize.meters.get("dirty", 0) + 1
        helper.meters["work"] = helper.meters.get("work", 0) + 1
    hero.memes["mischief"] = hero.memes.get("mischief", 0) + 1

    world.say(f"Then came a twist and a stitch of luck: {hero_name} saw a faux token glinting in the grass.")
    world.say(f"{hero_name} grabbed it at once, but the thing was only painted tin, and it made a silly clink-clank sound.")
    world.say(f"The fox sneezed at the noise, and even the hens seemed to laugh.")

    world.para()
    world.say(f"{helper_name} came near and said, “A faux shine is thin; real care is worth a grin.”")
    world.say(f"She wiped the {prize_cfg.label}, set the faux token aside, and showed {hero_name} a kinder game: gather leaves, count bees, and hum.")
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    hero.memes["calm"] = 1
    prize.meters["clean"] = 1
    if "dirty" in prize.meters:
        prize.meters["dirty"] = 0
    helper.meters["work"] = helper.meters.get("work", 0) + 1

    world.say(f"So {hero_name} did not keep the faux thing; instead, {hero.pronoun().capitalize()} laughed and helped with the leaves.")
    world.say(f"And by dusk the {prize_cfg.label} was clean, the lane was neat, and the little song had turned from trouble to cheer.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        faux=faux,
        setting=setting,
        activity=activity,
        resolved=True,
    )
    return world


SETTINGS = {
    "village": Setting(place="the village green", detail="green was bright with carts and chatter", affords={"tuft"}),
    "hedge": Setting(place="the hedge lane", detail="hedge lane was narrow and windy", affords={"tuft"}),
    "barn": Setting(place="the old barnyard", detail="barnyard was full of straw and peeping hens", affords={"tuft"}),
}

ACTIVITIES = {
    "tuft": Activity(
        id="tuft",
        verb="pluck a tuft from the hay",
        gerund="plucking tufts of hay",
        rush="rush to the haystack",
        mess="dusty",
        soil="dusty and rough",
        zone={"hands", "torso"},
        keyword="tuft",
        rhyme="tuft and puff",
        tags={"tuft", "humor", "folk"},
    ),
    "basket": Activity(
        id="basket",
        verb="tip the basket on the ground",
        gerund="tipping baskets and skipping jacks",
        rush="run to the basket",
        mess="strawy",
        soil="strawy and mussed",
        zone={"hands", "torso"},
        keyword="basket",
        rhyme="basket and task-it",
        tags={"humor", "folk"},
    ),
}

PRIZES = {
    "shawl": Prize(label="shawl", phrase="a wool shawl with a silver pin", region="torso"),
    "cap": Prize(label="cap", phrase="a little cap with a red ribbon", region="head"),
    "apron": Prize(label="apron", phrase="a clean apron with a pocket", region="torso"),
}

GEAR = [
    Gear(id="cloth", label="a clean cloth", covers={"torso"}, guards={"dusty", "strawy"}, prep="wrap the prize in a clean cloth", tail="wrapped it in the cloth"),
    Gear(id="capcover", label="a deep hood", covers={"head"}, guards={"dusty"}, prep="set on a deep hood", tail="pulled the hood low"),
]

NAMES = ["Milo", "Jory", "Nina", "Tessa", "Pip", "Bess", "Mara"]
HELPERS = ["Grandma Wren", "Aunt Sela", "Old Nan", "Grandma Brin"]


def valid_combos():
    combos = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale with the words "tuft", "ignore", and "faux".',
        f"Tell a humorous village story where {f['hero'].id} wants to {f['activity'].verb} but ignores a warning about {f['prize'].label}.",
        f"Write a rhyming, repetitive story about a faux object, a small mistake, and a kind grandmother who fixes the trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id} wanted to {act.verb}, even after {helper.id} warned {hero.id} about the {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} ignore?",
            answer=f"{hero.id} ignored {helper.id}'s warning and kept going toward the {act.rush}.",
        ),
        QAItem(
            question=f"What was the faux thing in the story?",
            answer="The faux thing was only a shiny fake token, not a real treasure.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} by the end?",
            answer=f"The {prize.label} was clean again, because {helper.id} wiped it and put the silly trouble aside.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tuft?",
            answer="A tuft is a small clump of hair, wool, grass, or feathers that sticks up from the rest.",
        ),
        QAItem(
            question="What does ignore mean?",
            answer="To ignore something means not to pay attention to it, even when someone tells you about it.",
        ),
        QAItem(
            question="What does faux mean?",
            answer="Faux means fake or not real, made to look like the real thing.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R), splashes(A,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protects(_,A,P).
#show valid/3.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world with tuft, ignore, and faux.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
        combos = [c for c in combos if (args.place is None or c[0] == args.place)
                  and (args.activity is None or c[1] == args.activity)
                  and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.hero, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        if isinstance(e, Character):
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            lines.append(f"  {e.id} ({e.role}) {' '.join(bits)}")
        else:
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.faux:
                bits.append("faux=True")
            if e.region:
                bits.append(f"region={e.region}")
            lines.append(f"  {e.id} ({e.label}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="village", activity="tuft", prize="shawl", hero="Milo", helper="Grandma Wren"),
    StoryParams(place="hedge", activity="tuft", prize="cap", hero="Nina", helper="Old Nan"),
    StoryParams(place="barn", activity="tuft", prize="apron", hero="Pip", helper="Aunt Sela"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
