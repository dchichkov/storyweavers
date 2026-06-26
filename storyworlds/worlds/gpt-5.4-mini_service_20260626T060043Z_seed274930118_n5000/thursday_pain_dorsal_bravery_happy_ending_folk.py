#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thursday_pain_dorsal_bravery_happy_ending_folk.py
============================================================================================================================

A small folk-tale story world about a Thursday errand, a sore dorsal fin,
bravery, and a happy ending.

Seed image:
- On a Thursday, a little river folk character notices a wounded dorsal fin.
- A kind helper wants to act bravely, but the hurt creature is in pain.
- They fetch a salve, a leaf bandage, and a bit of courage.
- The ending proves the hurt eased and the village grew a little braver.

This world is intentionally small and constraint-driven: it only generates
stories where the hero has a real reason to be brave and where the chosen aid
actually fits the injury.
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
    wound: str = ""
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Setting:
    place: str
    river: bool = False
    folk: bool = True


@dataclass
class Injury:
    id: str
    label: str
    region: str
    pain: str
    cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    eases: set[str]
    regions: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_ask_brave(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("fear", 0.0) >= THRESHOLD and ("brave_turn", hero.id) not in world.fired:
        world.fired.add(("brave_turn", hero.id))
        hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
        out.append(f"{hero.id} steadied their knees and took one brave breath.")
    return out


CAUSAL_RULES = [_r_ask_brave]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule(world)
            if sent:
                changed = True
                for s in sent:
                    world.say(s)


def injury_at_risk(injury: Injury, aid: Aid) -> bool:
    return injury.region in aid.regions


def compatible_aid(injury: Injury) -> Aid:
    for aid in AIDS:
        if injury.id in aid.eases and injury.region in aid.regions:
            return aid
    raise StoryError("No reasonable aid fits this injury.")


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.river:
            lines.append(asp.fact("river_setting", sid))
    for iid, inj in INJURIES.items():
        lines.append(asp.fact("injury", iid))
        lines.append(asp.fact("wound_on", iid, inj.region))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for w in sorted(aid.eases):
            lines.append(asp.fact("eases", aid.id, w))
        for r in sorted(aid.regions):
            lines.append(asp.fact("covers", aid.id, r))
    for loc in SETTINGS:
        for i in INJURIES:
            lines.append(asp.fact("possible", loc, i))
    return "\n".join(lines)


ASP_RULES = r"""
injury_risk(I,A) :- wound_on(I,R), covers(A,R).
good_fix(I,A) :- injury_risk(I,A), eases(A,I).
valid_story(L,I,A) :- possible(L,I), good_fix(I,A).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_story_triples())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    place: str
    injury: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


SETTINGS = {
    "riverbank": Setting(place="the riverbank", river=True),
    "cottage": Setting(place="the cottage green", river=False),
    "village": Setting(place="the village lane", river=False),
}

INJURIES = {
    "dorsal_scrape": Injury(
        id="dorsal_scrape",
        label="dorsal scrape",
        region="dorsal",
        pain="pain",
        cause="a thorny branch",
        tags={"dorsal", "pain"},
    ),
    "fin_sore": Injury(
        id="fin_sore",
        label="sore dorsal fin",
        region="dorsal",
        pain="pain",
        cause="a snag on a reed",
        tags={"dorsal", "pain"},
    ),
}

AIDS = [
    Aid(
        id="leaf_wrap",
        label="a cool leaf wrap",
        phrase="broad leaves and a soft strip of reed",
        eases={"dorsal_scrape", "fin_sore"},
        regions={"dorsal"},
        prep="gather broad leaves and make a leaf wrap",
        tail="tied the leaves gently around the sore dorsal place",
    ),
    Aid(
        id="moon_salve",
        label="moon salve",
        phrase="a little jar of pale salve",
        eases={"dorsal_scrape", "fin_sore"},
        regions={"dorsal"},
        prep="bring the moon salve from the shelf",
        tail="smoothed the salve over the hurt place",
    ),
]

HEROES = [
    ("Mira", "girl"),
    ("Tom", "boy"),
    ("Pip", "child"),
]
HELPERS = [
    ("Grandma Reed", "woman"),
    ("Uncle Bram", "man"),
    ("Old Nettle", "child"),
]


def valid_story_triples() -> list[tuple]:
    return [(p, i, a.id) for p in SETTINGS for i in INJURIES for a in AIDS if injury_at_risk(INJURIES[i], a)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about Thursday bravery and a dorsal injury.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--injury", choices=INJURIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "child"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man", "child"])
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
    if args.injury:
        injury = INJURIES[args.injury]
        if not any(injury_at_risk(injury, a) for a in AIDS):
            raise StoryError("The chosen injury has no reasonable aid.")
    combos = valid_story_triples()
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.injury is None or c[1] == args.injury)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, injury, _ = rng.choice(sorted(combos))
    hero_name, hero_type = (args.hero_name, args.hero_type) if args.hero_name and args.hero_type else rng.choice(HEROES)
    helper_name, helper_type = (args.helper_name, args.helper_type) if args.helper_name and args.helper_type else rng.choice(HELPERS)
    return StoryParams(place=place, injury=injury, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    injury = world.add(Entity(id="injury", type="thing", label=INJURIES[params.injury].label, region="dorsal"))
    aid = compatible_aid(INJURIES[params.injury])

    world.say(f"On a Thursday, {hero.label} walked by {world.setting.place} and saw a small hurt creature holding still from {INJURIES[params.injury].pain}.")
    world.say(f"The sore spot was on the dorsal side, and that made every little movement sting.")
    world.say(f"{hero.label} felt a brave wish wake up in their chest, even though the sight of the wound caused a pang of fear.")
    world.para()
    world.say(f"{hero.label} called to {helper.label}, and together they knew they must be brave and kind.")
    world.say(f"They chose {aid.label} because {aid.phrase} could help a dorsal hurt.")
    world.say(f"{helper.label.capitalize()} said, 'Do not fret; we will mend this pain with steady hands.'")
    hero.memes["bravery"] = 1.0
    hero.memes["fear"] = 1.0
    hero.memes["care"] = 1.0
    propagate(world)
    world.para()
    injury.meters["pain"] = 1.0
    hero.meters["help"] = 1.0
    world.say(f"They went to work by lantern light.")
    world.say(f"{aid.prep.capitalize()}, and {aid.tail}.")
    injury.meters["pain"] = 0.0
    hero.memes["bravery"] = 2.0
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.say(f"By the end, the pain had eased, the dorsal place was safe, and the little folk could smile again.")
    world.say(f"It was a happy ending: the brave act had made the Thursday feel warm all the way home.")
    world.facts = {
        "hero": hero,
        "helper": helper,
        "injury": injury,
        "aid": aid,
        "params": params,
        "place": params.place,
        "injury_id": params.injury,
    }
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a folk-tale story about a Thursday, bravery, pain, and a happy ending.',
        f"Tell a short story where {p.hero_name} and {p.helper_name} help a hurt creature with a dorsal injury.",
        "Write a child-friendly folk tale that ends with courage and healing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    injury = INJURIES[f["injury_id"]]
    aid = f["aid"]
    return [
        QAItem(
            question=f"What day did {p.hero_name} find the hurt creature?",
            answer="It was Thursday, a working day in the folk tale when the brave helping began.",
        ),
        QAItem(
            question=f"Where was the hurt place on the creature?",
            answer=f"The hurt place was on the dorsal side, so the pain was on the back area rather than the belly.",
        ),
        QAItem(
            question=f"How did they help the injury?",
            answer=f"They used {aid.label} because {aid.phrase} could soothe a dorsal hurt and ease the pain.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The pain eased, the brave wish turned into action, and the story ended in a happy ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dorsal mean?",
            answer="Dorsal means the back side of an animal or creature.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the choice to do a hard thing even when you feel afraid.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the trouble is solved and the characters finish in a good place.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {e.label or e.id} {' '.join(bits)}")
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
    StoryParams(place="riverbank", injury="fin_sore", hero_name="Mira", hero_type="girl", helper_name="Grandma Reed", helper_type="woman"),
    StoryParams(place="cottage", injury="dorsal_scrape", hero_name="Tom", hero_type="boy", helper_name="Uncle Bram", helper_type="man"),
    StoryParams(place="village", injury="fin_sore", hero_name="Pip", hero_type="child", helper_name="Old Nettle", helper_type="child"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
