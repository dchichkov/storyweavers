#!/usr/bin/env python3
"""
storyworlds/worlds/heed_optimum_kindness_pirate_tale.py
========================================================

A small pirate-tale storyworld about a crew member learning to heed a warning
and choose the optimum kind way to solve a problem.

The seed image is a gentle pirate tale: a young pirate wants treasure glory,
but the captain asks them to heed the safest path. The turn is not a duel or
a chase; it is a kindness choice that changes the ship's state and the crew's
mood.

World model:
- meters: physical quantities such as scraped wood, full sails, repaired gear
- memes: emotional quantities such as pride, worry, trust, kindness

The prose is state-driven: the captain can predict harm, the crew can respond
with a kinder plan, and the ending image proves what changed.
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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pirate", "mate"}
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
    sea: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class KindFix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.lines = [[]]
        c.fired = set(self.fired)
        c.weather = self.weather
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    crew_role: str
    seed: Optional[int] = None


SETTINGS = {
    "dock": Setting(place="the harbor dock", sea="calm", affords={"sail", "row"}),
    "cove": Setting(place="the quiet cove", sea="breezy", affords={"sail", "row"}),
    "deck": Setting(place="the deck", sea="windy", affords={"sail"}),
    "island": Setting(place="the little island", sea="sunny", affords={"row", "dig"}),
}

ACTIONS = {
    "sail": Action(
        id="sail",
        verb="sail through the reef",
        gerund="sailing through the reef",
        rush="rush toward the reef",
        risk="scrape the hull and snap the rope",
        weather="windy",
        keyword="heed",
        tags={"sea", "rope"},
    ),
    "row": Action(
        id="row",
        verb="row past the rocks",
        gerund="rowing past the rocks",
        rush="dash toward the rocks",
        risk="bump the boat and spill the crates",
        weather="breezy",
        keyword="optimum",
        tags={"sea", "wood"},
    ),
    "dig": Action(
        id="dig",
        verb="dig for buried coins",
        gerund="digging for buried coins",
        rush="scramble for the sand hill",
        risk="stir up the sand and lose the map",
        weather="sunny",
        keyword="kindness",
        tags={"sand", "map"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a folded treasure map", type="map", location="pocket"),
    "flag": Prize(label="flag", phrase="a bright ship flag", type="flag", location="mast"),
    "rope": Prize(label="rope", phrase="a coiled rescue rope", type="rope", location="deck"),
    "lantern": Prize(label="lantern", phrase="a brass lantern", type="lantern", location="hook"),
}

FIXES = [
    KindFix(
        id="slow_sail",
        label="a slower sail",
        prep="raise a gentler sail first",
        tail="set the gentler sail and glided by the reef",
        guards={"sea"},
        covers={"mast", "deck"},
    ),
    KindFix(
        id="wrap_rope",
        label="a rope wrap",
        prep="wrap the rope tight and ask the crew to move carefully",
        tail="wrapped the rope and kept the deck safe",
        guards={"wood"},
        covers={"deck"},
    ),
    KindFix(
        id="lantern_cover",
        label="a cloth lantern cover",
        prep="cover the lantern with a soft cloth first",
        tail="covered the lantern and kept its glass safe",
        guards={"sand"},
        covers={"hook"},
    ),
]

NAMES = ["Mina", "Pip", "Jory", "Nell", "Toma", "Cora", "Bram", "Wren"]
ROLES = ["mate", "sailor", "pirate"]


def risky(action: Action, prize: Prize) -> bool:
    return (action.id, prize.label) in {
        ("sail", "flag"),
        ("sail", "rope"),
        ("row", "map"),
        ("row", "lantern"),
        ("dig", "map"),
        ("dig", "rope"),
    }


def select_fix(action: Action, prize: Prize) -> Optional[KindFix]:
    for fx in FIXES:
        if action.id == "sail" and prize.label in {"flag", "rope"} and fx.id == "slow_sail":
            return fx
        if action.id == "row" and prize.label in {"map", "lantern"} and fx.id == "wrap_rope":
            return fx
        if action.id == "dig" and prize.label == "lantern" and fx.id == "lantern_cover":
            return fx
    return None


def predict(world: World, hero: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    prize = sim.get(prize_id)
    return {
        "harmed": prize.meters.get("scratched", 0) >= THRESHOLD or prize.meters.get("dirty", 0) >= THRESHOLD,
        "worry": sum(e.memes.get("worry", 0) for e in sim.characters()),
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    actor.memes["bold"] = actor.memes.get("bold", 0) + 1
    if action.id == "sail":
        world.facts["reef_seen"] = True
        world.say(f"The wind pushed at the sails.")
    elif action.id == "row":
        world.facts["rocks_seen"] = True
        world.say(f"The oars tapped the water in a steady beat.")
    else:
        world.facts["sand_seen"] = True
        world.say(f"The sand sparkled where the little shovel landed.")


def tell(setting: Setting, action: Action, prize_cfg: Prize, name: str, role: str) -> World:
    world = World(setting)
    world.weather = action.weather

    hero = world.add(Entity(id=name, kind="character", type="pirate", label=name))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="the captain"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=captain.id,
    ))

    hero.memes["pride"] = 1
    hero.memes["kindness"] = 0
    captain.memes["trust"] = 0

    world.say(f"{hero.id} was a little {role} who loved the sea and the shine of treasure.")
    world.say(f"{hero.id} carried {prize.phrase} because {prize.label} made the ship feel lucky.")
    world.para()
    world.say(f"One day at {setting.place}, the sky was {setting.sea} and the crew was ready to go.")
    world.say(f"{hero.id} wanted to {action.verb}, even though the captain could see a problem ahead.")
    pred = predict(world, hero, action, prize.id)
    if risky(action, prize):
        world.say(
            f'"Heed me," said the captain. "If you go now, you could {action.risk}, '
            f"and that would not be kind to the ship."
        )
        hero.memes["worry"] = 1
        hero.memes["defiance"] = 1
        world.say(f"{hero.id} paused, then glanced at the {prize.label} and at the captain's face.")
        world.say(f"{hero.id} did not want trouble; {hero.id} wanted the optimum way to keep everyone safe.")
        fix = select_fix(action, prize)
        world.para()
        if fix is None:
            raise StoryError("No kind fix fits this pirate problem.")
        hero.memes["kindness"] += 1
        captain.memes["trust"] += 1
        if action.id == "sail":
            world.say(f'{hero.id} said, "Aye, let us heed the warning and choose the optimum course."')
        elif action.id == "row":
            world.say(f'{hero.id} said, "Aye, let us heed the warning and choose the optimum course."')
        else:
            world.say(f'{hero.id} said, "Aye, let us heed the warning and choose the optimum course."')
        world.say(f"They chose {fix.label} and followed {fix.prep}.")
        _do_action(world, hero, action, narrate=True)
        if prize.label == "map":
            prize.meters["safe"] = 1
        else:
            prize.meters["safe"] = 1
        world.say(f"That kept {prize.phrase} safe, and the crew smiled with relief.")
        world.say(f"In the end, {fix.tail}, and the captain praised {hero.id}'s kindness.")
    else:
        world.say(f"There was no real danger, so the captain let {hero.id} go on.")
        _do_action(world, hero, action, narrate=True)
        world.say(f"The day stayed calm, and {prize.phrase} was never at risk.")

    world.facts.update(hero=hero, captain=captain, prize=prize, prize_cfg=prize_cfg, action=action, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["action"], f["prize_cfg"]
    return [
        f'Write a short pirate tale for a child that includes the word "{act.keyword}" and the idea of heed.',
        f"Tell a gentle pirate story where {hero.id} wants to {act.verb} but the captain worries about {prize.phrase}.",
        f"Write a simple sea story that ends with kindness solving a problem on the ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, action = f["hero"], f["captain"], f["prize"], f["action"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {action.verb} because the sea looked exciting.",
        ),
        QAItem(
            question=f"Why did the captain ask {hero.id} to heed the warning?",
            answer=f"The captain could see that going ahead would {action.risk}, which could hurt the ship or the gear.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem in a kind way?",
            answer=f"{hero.id} chose the optimum kind plan, followed the captain's warning, and used the safer fix so {prize.phrase} stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    out: list[QAItem] = []
    if "sea" in tags:
        out.append(QAItem(
            question="What is a reef?",
            answer="A reef is a rough, shallow place in the sea where rocks or coral can poke up near the water."
        ))
    if "rope" in tags:
        out.append(QAItem(
            question="What is rope used for on a ship?",
            answer="Rope helps tie things down, hold sails, and keep gear from sliding around."
        ))
    if "sand" in tags:
        out.append(QAItem(
            question="What is sand?",
            answer="Sand is made of tiny grains of rock, and it can get into shoes, pockets, and tools."
        ))
    out.append(QAItem(
        question="What does kindness mean?",
        answer="Kindness means choosing to help, protect, and care about other people instead of only thinking about yourself."
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="dock", action="sail", prize="flag", name="Mina", crew_role="mate"),
    StoryParams(place="cove", action="row", prize="map", name="Pip", crew_role="pirate"),
    StoryParams(place="island", action="dig", prize="lantern", name="Nell", crew_role="mate"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle pirate tale storyworld about heed and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--crew-role", choices=ROLES)
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
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(sorted(SETTINGS[place].affords))
    prize = args.prize or rng.choice(list(PRIZES))
    if args.action and args.prize and not risky(ACTIONS[args.action], PRIZES[args.prize]):
        raise StoryError("That pirate problem is too weak: the prize is not truly at risk.")
    if action not in SETTINGS[place].affords:
        raise StoryError("That place cannot support that pirate action.")
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        crew_role=args.crew_role or rng.choice(ROLES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], params.name, params.crew_role)
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
risky(sail, flag).
risky(sail, rope).
risky(row, map).
risky(row, lantern).
risky(dig, map).
risky(dig, rope).

fix(sail, flag, slow_sail).
fix(sail, rope, slow_sail).
fix(row, map, wrap_rope).
fix(row, lantern, wrap_rope).
fix(dig, lantern, lantern_cover).

valid(P,A,Pr) :- affords(P,A), risky(A,Pr), fix(A,Pr,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for pr in PRIZES:
        lines.append(asp.fact("prize", pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                if risky(ACTIONS[act], PRIZES[prize]):
                    combos.append((place, act, prize))
    return sorted(combos)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid pirate tales:")
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
