#!/usr/bin/env python3
"""
storyworlds/worlds/wonder_cocoon_virgin_quest_friendship_suspense_comedy.py
============================================================================

A small, self-contained storyworld about a whimsical quest in a virgin meadow,
where a cocoon, friendship, suspense, and comedy all matter.

Premise:
- A curious young hero and a tiny friend need to cross an untouched place to
  deliver a simple object.
- A cocoon appears at the center of the quest, and everyone wonders what is
  inside.
- Suspense grows because opening it too soon would spoil the surprise.
- Friendship and careful waiting resolve the tension, and the ending image
  proves the change: the cocoon opens, the quest succeeds, and the friends
  laugh together.

This module follows the Storyweavers contract:
- self-contained stdlib script
- eager results import
- lazy ASP import inside helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- QA, JSON, trace, ASP, verify, show-asp support
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    place: str = "the virgin meadow"
    affords: set[str] = field(default_factory=set)
    description: str = ""


@dataclass
class Quest:
    id: str
    goal: str
    action: str
    hurry: str
    risk: str
    reveal: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _apply_suspense(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    cocoon = world.get(world.facts["cocoon"].id)
    if hero.memes.get("curiosity", 0.0) >= THRESHOLD and cocoon.meters.get("mystery", 0.0) >= THRESHOLD:
        sig = ("suspense", hero.id, cocoon.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
            out.append(f"Everyone held their breath and wondered what was inside the cocoon.")
    return out


def _apply_reveal(world: World) -> list[str]:
    out: list[str] = []
    cocoon = world.get(world.facts["cocoon"].id)
    if cocoon.meters.get("cracked", 0.0) >= THRESHOLD:
        sig = ("reveal", cocoon.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(world.facts["reveal_line"])
    return out


CAUSAL_RULES = [
    _apply_suspense,
    _apply_reveal,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.risk in gear.guards and prize.region in gear.covers:
            return gear
    return None


def quest_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.tags


def predict_reveal(world: World, hero: Entity, quest: Quest, cocoon: Entity) -> bool:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    return sim.get(cocoon.id).meters.get("cracked", 0.0) >= THRESHOLD


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.meters["steps"] = hero.meters.get("steps", 0.0) + 1
    world.zone = set(quest.tags)
    cocoon = world.get(world.facts["cocoon"].id)
    cocoon.meters["mystery"] = cocoon.meters.get("mystery", 0.0) + 1
    if hero.memes.get("friendship", 0.0) >= THRESHOLD:
        cocoon.meters["cracked"] = cocoon.meters.get("cracked", 0.0) + 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "meadow": Setting(
        place="the virgin meadow",
        affords={"butterfly_quest", "lantern_quest"},
        description="The grass was tall and untouched, and the path looked brand new.",
    ),
    "grove": Setting(
        place="the virgin grove",
        affords={"butterfly_quest", "lantern_quest"},
        description="The trees were quiet, and nobody had marked the path yet.",
    ),
    "hill": Setting(
        place="the virgin hill",
        affords={"butterfly_quest"},
        description="The hill was open and soft, with a funny breeze at the top.",
    ),
}

QUESTS = {
    "butterfly_quest": Quest(
        id="butterfly_quest",
        goal="deliver a ribbon to the cocoon",
        action="tiptoe to the cocoon",
        hurry="dash toward the cocoon",
        risk="startle",
        reveal="The cocoon gave a tiny pop, and a bright butterfly blinked out with a silly wiggle.",
        keyword="wonder",
        tags={"cocoon", "wonder", "friendship", "suspense", "comedy"},
    ),
    "lantern_quest": Quest(
        id="lantern_quest",
        goal="carry a seed cake to the cocoon",
        action="walk gently to the cocoon",
        hurry="rush toward the cocoon",
        risk="jostle",
        reveal="The cocoon cracked open, and a sleepy moth yawned so wide that everyone giggled.",
        keyword="cocoon",
        tags={"cocoon", "wonder", "friendship", "suspense", "comedy"},
    ),
}

PRIZES = {
    "ribbon": Prize(
        label="ribbon",
        phrase="a blue ribbon with a shiny knot",
        type="ribbon",
        region="torso",
    ),
    "cake": Prize(
        label="cake",
        phrase="a seed cake in a little tin",
        type="cake",
        region="hands",
    ),
    "jar": Prize(
        label="jar",
        phrase="a small jar of nectar",
        type="jar",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"jostle"},
        prep="put on soft gloves first",
        tail="went back for the soft gloves",
        plural=True,
    ),
    Gear(
        id="cape",
        label="a feather cape",
        covers={"torso"},
        guards={"startle"},
        prep="wrap on a feather cape first",
        tail="took the feather cape along",
    ),
]


GIRL_NAMES = ["Mina", "Luna", "Tia", "Nora", "Pia"]
BOY_NAMES = ["Eli", "Noah", "Toby", "Finn", "Owen"]
TRAITS = ["curious", "cheerful", "silly", "brave", "bouncy"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    friend_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whimsical quest storyworld with wonder, cocoon, virgin, friendship, suspense, and comedy.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = QUESTS[qid]
            for pid, prize in PRIZES.items():
                if quest_at_risk(quest, prize) and select_gear(quest, prize):
                    out.append((place, qid, pid, "girl"))
                    out.append((place, qid, pid, "boy"))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.prize:
        quest, prize = QUESTS[args.quest], PRIZES[args.prize]
        if not (quest_at_risk(quest, prize) and select_gear(quest, prize)):
            raise StoryError("That quest and prize do not make a reasonable story here.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or c[3] == args.gender)]
    if not combos:
        raise StoryError("No valid combination matches the requested options.")
    place, quest, prize, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, friend_name=friend_name)


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, gender: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={}))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend", label="friend", meters={}, memes={}))
    cocoon = world.add(Entity(id="cocoon", type="cocoon", label="cocoon", plural=False, meters={"mystery": 1.0}, memes={}))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    gear = select_gear(quest, prize_cfg)

    world.say(f"{hero.id} and {friend.id} loved the {setting.place}. {setting.description}")
    world.say(f"They were on a tiny quest to {quest.goal}, and the word {quest.keyword} made {hero.id} look up in wonder.")
    world.say(f"Near the path sat a cocoon. {hero.id} carried {prize_cfg.phrase}, and {friend.id} smiled at the funny little bundle.")

    world.para()
    world.say(f"At the edge of the virgin meadow, {hero.id} wanted to {quest.action}, but {friend.id} worried about the cocoon.")
    hero.memes["curiosity"] = 1.0
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts.update(hero=hero, friend=friend, cocoon=cocoon, prize=prize, quest=quest, gear=gear,
                       reveal_line=quest.reveal)

    world.say(f'"Let us be gentle," {friend.id} said, because the cocoon looked important and a bit suspenseful.')
    if predict_reveal(world, hero, quest, cocoon):
        world.say(f"{hero.id} nodded. The quest could wait for careful feet and a kinder plan.")
    _do_quest(world, hero, quest, narrate=True)

    world.para()
    if gear is not None:
        hero.memes["friendship"] += 1
        world.say(f"{friend.id} found {gear.label} and said, \"How about we {gear.prep} and help the cocoon feel safe?\"")
        world.say(f"{hero.id} laughed, put on the gear, and they {gear.tail}.")
        cocoon.meters["cracked"] = cocoon.meters.get("cracked", 0.0) + 1
        propagate(world, narrate=True)
    else:
        cocoon.meters["cracked"] = cocoon.meters.get("cracked", 0.0) + 1
        propagate(world, narrate=True)

    world.say(f"In the end, the cocoon opened, the quest was done, and {hero.id} and {friend.id} laughed at the little surprise.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short, funny story for young children about {f['hero'].id} and {f['friend'].id} on a quest in {world.setting.place}.",
        f"Tell a story with wonder and suspense where a cocoon is part of a friendship adventure and the ending makes everyone laugh.",
        f"Write a gentle comedy about a virgin meadow, a cocoon, and a small quest that ends in a happy reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, quest, prize = f["hero"], f["friend"], f["quest"], f["prize"]
    return [
        QAItem(
            question=f"Who went on the quest in {world.setting.place}?",
            answer=f"{hero.id} went with {friend.id} on a small friendship quest in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to do near the cocoon?",
            answer=f"{hero.id} wanted to {quest.action} while carrying {prize.phrase}.",
        ),
        QAItem(
            question="Why did the friends slow down instead of rushing to the cocoon?",
            answer="They slowed down because the cocoon felt special, and they wanted to keep the moment safe and full of wonder.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=f"The cocoon opened, {quest.reveal.lower()} Then the friends laughed together and the quest ended happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cocoon?",
            answer="A cocoon is a soft covering some insects make while they grow and change inside it.",
        ),
        QAItem(
            question="What is wonder?",
            answer="Wonder is the feeling you get when something seems surprising, beautiful, or hard to explain right away.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and enjoying time together.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A quest is reasonable when the prize is at risk and there is compatible gear.
quest_at_risk(Q, P) :- quest(Q), prize(P), risky(Q, R), region(P, R).
has_fix(Q, P) :- quest_at_risk(Q, P), gear(G), guards(G, M), risk_of(Q, M), covers(G, R), region(P, R).
valid(Place, Q, P, G) :- affords(Place, Q), quest_at_risk(Q, P), gear(G), has_fix(Q, P), wears(Gender, P), gender_ok(P, Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("tag", qid, t))
        lines.append(asp.fact("risk_of", qid, q.risk))
        lines.append(asp.fact("risky", qid, q.risk))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
            lines.append(asp.fact("gender_ok", pid, g))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(a, b, c, d) for (a, b, c, d) in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], PRIZES[params.prize], params.name, params.gender, params.friend_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
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
    StoryParams(place="meadow", quest="butterfly_quest", prize="ribbon", name="Mina", gender="girl", friend_name="Eli"),
    StoryParams(place="grove", quest="lantern_quest", prize="cake", name="Noah", gender="boy", friend_name="Tia"),
    StoryParams(place="hill", quest="butterfly_quest", prize="jar", name="Luna", gender="girl", friend_name="Owen"),
]


def explain_rejection() -> str:
    return "No story: that combination does not produce a safe, funny quest in this world."


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [build_story(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = build_story(params)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
