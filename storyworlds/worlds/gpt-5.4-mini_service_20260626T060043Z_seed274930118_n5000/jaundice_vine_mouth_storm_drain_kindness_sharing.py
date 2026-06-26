#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/jaundice_vine_mouth_storm_drain_kindness_sharing.py
=============================================================================================================================

A small nursery-rhyme-style story world set in a storm drain, built from the
seed words jaundice, vine, and mouth, with Kindness and Sharing as the guiding
features.

Premise:
- A little creature lives near a storm drain opening.
- A long vine slips into the drain and begins to tangle and clog the way.
- The hero notices a yellow, jaundice-like tint and a sore mouth from worry
  and thirst after the stormy air.
- Kindness and Sharing help the hero and a neighbor solve the problem together.

The story keeps state-driven prose: wetness, blockage, thirst, relief, and the
social turn from worry to help.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("wet", "blocked", "clean", "dry", "safe", "sick"):
            self.meters.setdefault(k, 0.0)
        for k in ("kindness", "sharing", "worry", "relief", "joy", "thirst"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the storm drain"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Help:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
    plural: bool = False


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "storm_drain": Setting(place="the storm drain", affords={"drift", "clear"}),
}

ACTIVITIES = {
    "drift": Activity(
        id="drift",
        verb="drift through the storm drain",
        gerund="drifting by the drain",
        rush="dash into the drain water",
        mess="wet",
        soil="wet and shaky",
        keyword="storm",
        tags={"storm", "wet"},
    ),
    "clear": Activity(
        id="clear",
        verb="clear the storm drain",
        gerund="clearing the drain",
        rush="push the mess away",
        mess="blocked",
        soil="clogged",
        keyword="drain",
        tags={"drain", "help"},
    ),
}

HELPERS = [
    Help(
        id="broom",
        label="a little broom",
        phrase="a little broom with a bright handle",
        covers={"ground"},
        guards={"blocked"},
        prep="share a little broom",
        tail="shared the little broom and swept together",
    ),
    Help(
        id="bucket",
        label="a bucket",
        phrase="a bucket for carrying water",
        covers={"hands"},
        guards={"wet"},
        prep="share a bucket",
        tail="shared the bucket and carried the water away",
    ),
]

PRIZES = {
    "lantern": Entity(id="lantern", type="thing", label="lantern", phrase="a small lantern"),
    "cloak": Entity(id="cloak", type="thing", label="cloak", phrase="a warm little cloak"),
}

HERO_NAMES = ["Nell", "Milo", "Pip", "Luna", "Toby", "Maya"]
NEIGHBOR_NAMES = ["Dot", "Ben", "Rose", "Finn"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    neighbor: str
    seed: Optional[int] = None


def blocked_by_vine(world: World) -> bool:
    return world.entities["vine"].meters["blocked"] >= THRESHOLD


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if world.entities["vine"].meters["blocked"] >= THRESHOLD and ("blocked",) not in world.fired:
        world.fired.add(("blocked",))
        out.append("The vine made the drain too tight, and water could not go through.")
    if world.entities["mender"].memes["kindness"] >= THRESHOLD and world.entities["mender"].memes["sharing"] >= THRESHOLD:
        if world.entities["vine"].meters["blocked"] >= THRESHOLD and ("help",) not in world.fired:
            world.fired.add(("help",))
            world.entities["vine"].meters["blocked"] = 0
            world.entities["drain"].meters["safe"] += 1
            world.entities["mender"].memes["relief"] += 1
            out.append("Kindness and Sharing let the little hands clear the vine away.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World) -> dict:
    sim = world.copy()
    sim.entities["vine"].meters["blocked"] = 1
    propagate(sim, narrate=False)
    return {
        "clears": sim.entities["vine"].meters["blocked"] < THRESHOLD,
        "safe": sim.entities["drain"].meters["safe"] >= THRESHOLD,
    }


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="mouse", label=params.name))
    neighbor = world.add(Entity(id=params.neighbor, kind="character", type="mouse", label=params.neighbor))
    vine = world.add(Entity(id="vine", type="thing", label="vine", phrase="a green vine", meters={"blocked": 1.0}))
    drain = world.add(Entity(id="drain", type="thing", label="storm drain", phrase="the storm drain", meters={"safe": 0.0}))
    prize = world.add(Entity(id=params.prize, type="thing", label=params.prize, phrase=PRIZES[params.prize].phrase))

    world.facts.update(hero=hero, neighbor=neighbor, vine=vine, drain=drain, prize=prize, activity=ACTIVITIES[params.activity])

    world.say(f"Down by the {world.setting.place}, little {hero.id} sat in a cozy nook.")
    world.say(f"{hero.id} loved the hum of the rain and the hush of the stones.")
    world.say(f"Near the dark grate, a vine trailed down and twined and twirled.")

    if params.prize == "lantern":
        world.say(f"{hero.id} held a lantern, and its soft glow shone on {hero.pronoun('possessive')} mouth.")
    else:
        world.say(f"{hero.id} wore a warm cloak, but {hero.pronoun('possessive')} mouth felt dry from the storm air.")

    world.entities["mender"] = hero
    hero.memes["worry"] += 1
    hero.memes["thirst"] += 1
    world.say(f"Then {hero.id} noticed a jaundice-yellow tint on the vine, like butter in the rain.")
    world.say(f"{hero.id}'s mouth went small and worried; {hero.pronoun('possessive')} little heart said, 'Oh dear, oh dear.'")

    world.para()
    world.say(f"{neighbor.id} came by, gentle and bright, and asked if {hero.id} needed help.")
    world.say(f"{hero.id} said yes, and Sharing brought them close.")

    pred = predict(world)
    world.say(f"They saw the vine would clog the drain and stop the water if nobody cared.")
    world.say(f"{neighbor.id} offered Kindness, and {hero.id} offered Sharing.")
    hero.memes["kindness"] += 1
    hero.memes["sharing"] += 1
    neighbor.memes["kindness"] += 1
    neighbor.memes["sharing"] += 1

    if pred["clears"]:
        propagate(world, narrate=True)

    world.para()
    world.say(f"So {hero.id} and {neighbor.id} worked with a little broom and a bucket, side by side.")
    world.say(f"They lifted the vine, swept the grit, and let the storm drain breathe.")
    world.say(f"The water ran on, the stones grew quiet, and {hero.id}'s mouth felt cool and glad.")
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    if params.prize == "lantern":
        world.say(f"At the end, the lantern still glowed, and the vine no longer blocked the way.")
    else:
        world.say(f"At the end, the cloak stayed dry, and the drain shone clear in the rain.")
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a nursery-rhyme-style story about a child in a storm drain with a vine, a mouth, and a little yellow worry.',
        'Tell a gentle rhyme where Kindness and Sharing help two little neighbors clear a storm drain.',
        'Write a child-facing story that includes the words jaundice, vine, and mouth, and ends with the water flowing again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    neighbor = f["neighbor"]
    return [
        QAItem(
            question=f"Where is the story set?",
            answer="The story is set in the storm drain, down where the rainwater runs and the stones are wet.",
        ),
        QAItem(
            question=f"What did the vine do in the storm drain?",
            answer="The vine twined down and blocked the way, so the water could not go through until the children helped.",
        ),
        QAItem(
            question=f"Why did {hero.id} look worried at first?",
            answer=f"{hero.id} felt worried because the vine could clog the drain, and {hero.id}'s mouth felt dry and uneasy in the storm air.",
        ),
        QAItem(
            question=f"How did Kindness and Sharing help?",
            answer=f"Kindness and Sharing helped {hero.id} and {neighbor.id} work together with a broom and a bucket so the vine could be cleared away.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the drain was clear, the water ran on, and {hero.id} felt relieved and glad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, caring, and helpful to someone else.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use a toy, tool, or turn so you can help each other.",
        ),
        QAItem(
            question="What is a vine?",
            answer="A vine is a long, climbing plant that can twist around things as it grows.",
        ),
        QAItem(
            question="What is a storm drain for?",
            answer="A storm drain carries rainwater away so streets and paths do not flood too much.",
        ),
        QAItem(
            question="What is jaundice?",
            answer="Jaundice is a condition that can make skin or eyes look yellow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"{e.id}: {' '.join(bits) if bits else '(quiet)'}")
    return "\n".join(out)


ASP_RULES = r"""
blocked(vine) :- vine_blocked(vine).
helped(H) :- kindness(H), sharing(H).
cleared(D) :- drain(D), blocked(vine), helped(H).
#show blocked/1.
#show cleared/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("vine_blocked", "vine"), asp.fact("drain", "drain")]
    lines.append(asp.fact("kindness", "mender"))
    lines.append(asp.fact("sharing", "mender"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show blocked/1.\n#show cleared/1."))
    atoms = set((s.name, tuple(a.name if a.type != a.type.Number else a.number for a in s.arguments)) for s in model)
    py = {("blocked", ("vine",)), ("cleared", ("drain",))}  # expected if kindness/sharing present
    # The ASP program is intentionally simple; the parity check ensures it solves.
    if atoms == py:
        print("OK: ASP solved the story-world gate.")
        return 0
    print("MISMATCH:")
    print(" asp:", atoms)
    print(" py :", py)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world in a storm drain.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--neighbor", choices=NEIGHBOR_NAMES)
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
    place = args.place or "storm_drain"
    activity = args.activity or "clear"
    prize = args.prize or rng.choice(list(PRIZES))
    name = args.name or rng.choice(HERO_NAMES)
    neighbor = args.neighbor or rng.choice([n for n in NEIGHBOR_NAMES if n != name])
    if prize not in PRIZES:
        raise StoryError("Unknown prize.")
    return StoryParams(place=place, activity=activity, prize=prize, name=name, neighbor=neighbor)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(place="storm_drain", activity="clear", prize="lantern", name="Nell", neighbor="Dot"),
    StoryParams(place="storm_drain", activity="clear", prize="cloak", name="Pip", neighbor="Ben"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show blocked/1.\n#show cleared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show blocked/1.\n#show cleared/1."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
