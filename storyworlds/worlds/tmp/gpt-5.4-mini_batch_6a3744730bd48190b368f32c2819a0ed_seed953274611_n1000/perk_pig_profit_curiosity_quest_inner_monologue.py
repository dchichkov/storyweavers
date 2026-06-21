#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/perk_pig_profit_curiosity_quest_inner_monologue.py
==================================================================================

A tiny nursery-rhyme storyworld about a pig, a perk, and a profit quest.

Premise
-------
A curious little pig notices a shiny perk on a notice board, wonders whether a
small quest could bring a profit, and follows an inner monologue from doubt to
discovery. The world is state-driven: the pig's curiosity, the chosen quest, the
available perk, and the ending payoff all shape the prose.

The tone aims for a gentle nursery rhyme cadence:
- short, concrete beats
- repeated sounds and simple images
- a clear beginning, middle turn, and ending image

The required seed words are woven into the world:
- perk
- pig
- profit

The narrative instruments are modeled in state:
- Curiosity
- Quest
- Inner Monologue

This file is standalone and stdlib-only, with lazy ASP import only when needed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CURIOUS_MIN = 1.0
QUEST_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if "joy" not in self.meters:
            self.meters["joy"] = 0.0
        if "savings" not in self.meters:
            self.meters["savings"] = 0.0
        if "curiosity" not in self.memes:
            self.memes["curiosity"] = 0.0
        if "doubt" not in self.memes:
            self.memes["doubt"] = 0.0

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "pig":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    setting: str
    pig_name: str
    perk: str
    quest: str
    profit_goal: int = 3
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    rhyme: str
    board: str
    market: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Perk:
    id: str
    label: str
    phrase: str
    gleam: str
    cost: int
    bonus: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    task: str
    trail: str
    reward_line: str
    required_curiosity: int
    profit: int
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


SETTINGS = {
    "meadow": Setting(id="meadow", place="a green meadow", rhyme="where daisies nod and breezes blow",
                      board="a little notice board", market=False, tags={"field", "notice"}),
    "market": Setting(id="market", place="a busy market", rhyme="where baskets bump and lanterns glow",
                      board="a bright notice board", market=True, tags={"market", "notice"}),
    "harbor": Setting(id="harbor", place="a quiet harbor", rhyme="where ropes and sails all sway and go",
                      board="a salt-sprayed notice board", market=True, tags={"harbor", "notice"}),
}

PERKS = {
    "badge": Perk(id="badge", label="a shiny badge", phrase="a shiny badge",
                  gleam="gleamed like a star", cost=1, bonus=2, tags={"shiny", "badge"}),
    "bell": Perk(id="bell", label="a tiny bell", phrase="a tiny bell",
                 gleam="jangled clear and bright", cost=1, bonus=1, tags={"bell"}),
    "ribbon": Perk(id="ribbon", label="a ribbon token", phrase="a ribbon token",
                   gleam="fluttered in the light", cost=0, bonus=1, tags={"ribbon"}),
}

QUESTS = {
    "strawberries": Quest(id="strawberries", task="gather strawberries", trail="down the soft green hill",
                          reward_line="the stall keeper would pay a copper coin",
                          required_curiosity=1, profit=3, ending_image="a bowl of red strawberries",
                          tags={"berries", "field"}),
    "shells": Quest(id="shells", task="collect shells", trail="along the silver shore",
                    reward_line="the shell buyer would pay a tidy coin",
                    required_curiosity=1, profit=2, ending_image="a dish of pearly shells",
                    tags={"shore", "harbor"}),
    "buttons": Quest(id="buttons", task="sort buttons", trail="by the market stall",
                     reward_line="the peddler would pay a bright coin",
                     required_curiosity=1, profit=1, ending_image="a jar of buttons",
                     tags={"market", "stall"}),
}

PIG_NAMES = ["Pip", "Poppy", "Percy", "Penny", "Prue", "Pat"]


def curiosity_gate(perk: Perk, quest: Quest) -> bool:
    return perk.bonus >= 1 and quest.required_curiosity <= CURIOUS_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, perk in PERKS.items():
            for qid, quest in QUESTS.items():
                if curiosity_gate(perk, quest):
                    combos.append((sid, pid, qid))
    return combos


def choose_reasonable_perk(quest: Quest) -> Perk:
    return max(PERKS.values(), key=lambda p: (p.bonus, -p.cost))


def initial_inner_monologue(world: World, pig: Entity, perk: Perk, quest: Quest, setting: Setting) -> None:
    world.say(
        f"On a bright little day in {setting.place}, {pig.id} trotted by "
        f"{setting.board}. {pig.id} saw {perk.phrase}; it {perk.gleam}."
    )
    world.say(
        f'"A perk, a perk," thought {pig.id}. "What a fine small perk! '
        f'Could a quest bring a profit?"'
    )
    pig.memes["curiosity"] += 1.0
    pig.memes["doubt"] += 0.5


def _r_curiosity(world: World) -> list[str]:
    out = []
    pig = world.get("pig")
    if pig.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("curious",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pig.meters["steps"] = pig.meters.get("steps", 0.0) + 1.0
    out.append("Its little hooves pattered on, and the wondering grew warm.")
    return out


def _r_profit(world: World) -> list[str]:
    out = []
    pig = world.get("pig")
    quest = world.get("quest")
    if pig.meters.get("steps", 0.0) < THRESHOLD:
        return out
    sig = ("profit",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pig.meters["savings"] += quest.attrs["profit"]
    out.append("The quest paid its small coin, and the pocket grew plump.")
    return out


CAUSAL_RULES = [Rule("curiosity", _r_curiosity), Rule("profit", _r_profit)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def do_quest(world: World, pig: Entity, perk: Perk, quest: Quest, setting: Setting) -> None:
    world.say(
        f'"I shall go," thought {pig.id}, "for a quest can be merry, '
        f'and profit can buy a treat."'
    )
    world.say(
        f"{pig.id} set off {quest.trail}, with {perk.label} tucked close and "
        f"{quest.reward_line}."
    )
    pig.meters["perk"] += perk.bonus
    pig.attrs["perk"] = perk.label
    pig.attrs["quest"] = quest.task
    pig.meters["joy"] += 1
    propagate(world, narrate=True)


def finish(world: World, pig: Entity, quest: Quest, setting: Setting) -> None:
    world.para()
    world.say(
        f"{pig.id} came home with a grin. In the end, there was {quest.ending_image} "
        f"and a coin or two to show."
    )
    if pig.meters["savings"] >= quest.profit:
        world.say(
            f'"A profit, a profit," thought {pig.id}, "small as a plum, but sweet as can be."'
        )
    world.say(
        f"And under the moon in {setting.place}, {pig.id} curled up small, "
        f"happy with {pig.pronoun("possessive")} fine little perk."
    )
    pig.meters["joy"] += 1


def tell(setting: Setting, perk: Perk, quest: Quest, pig_name: str) -> World:
    world = World()
    pig = world.add(Entity(id=pig_name, kind="character", type="pig", role="hero", label="the pig"))
    world.add(Entity(id="perk", kind="thing", type="perk", label=perk.label))
    qent = world.add(Entity(id="quest", kind="thing", type="quest", label=quest.task, attrs={"profit": quest.profit}))
    world.facts["setting"] = setting
    world.facts["perk"] = perk
    world.facts["quest"] = quest
    initial_inner_monologue(world, pig, perk, quest, setting)
    world.para()
    world.say(
        f"{pig.id} looked at {setting.board} and at the trail ahead."
    )
    do_quest(world, pig, perk, quest, setting)
    finish(world, pig, quest, setting)
    world.facts.update(pig=pig, qent=qent, outcome="profitable" if pig.meters["savings"] >= quest.profit else "plain")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the words "perk", "pig", and "profit" in a gentle quest.',
        f"Tell a small story about {f['pig'].id}, a pig who notices {f['perk'].label} and thinks about profit.",
        f'Write a rhyme where curiosity leads a pig on a quest and the ending feels like a tiny profit.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    pig = f["pig"]
    perk = f["perk"]
    quest = f["quest"]
    qa = [
        ("Who is the story about?",
         f"It is about {pig.id}, a curious little pig. The pig notices a perk and begins to wonder what profit might mean."),
        ("What did the pig wonder about?",
         f"{pig.id} wondered whether a quest could bring a profit. That thought pushed the little pig to follow the trail and see for itself."),
        ("What happened on the quest?",
         f"{pig.id} went down the trail, did the task, and came home with a small profit. The perk stayed part of the happy memory, like a bright little sign."),
    ]
    if world.facts["outcome"] == "profitable":
        qa.append((
            "How did the story end?",
            f"It ended with a small profit and a cheerful pig. The ending image shows {pig.id} home again, pleased with the quest and the perk."
        ))
    return qa


KNOWLEDGE = {
    "pig": [("What is a pig?",
             "A pig is a farm animal with a round snout and curly tail. Pigs can be curious and love to root around for food.")],
    "curiosity": [("What is curiosity?",
                    "Curiosity is the feeling that makes you want to look, ask, and learn more. It can lead you on a quest for answers.")],
    "quest": [("What is a quest?",
               "A quest is a little journey or task done to reach a goal. In stories, a quest often has a beginning, a middle, and a reward at the end.")],
    "profit": [("What is profit?",
                "Profit is what is left after you gain more than you spend. It can be a small win, like a few coins after a good task.")],
    "perk": [("What is a perk?",
               "A perk is a nice extra benefit or treat. It is something pleasant that makes the day feel brighter.")],
}
KNOWLEDGE_ORDER = ["pig", "curiosity", "quest", "profit", "perk"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pig", "curiosity", "quest", "profit", "perk"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="meadow", pig_name="Pip", perk="badge", quest="strawberries", profit_goal=3, seed=None),
    StoryParams(setting="market", pig_name="Poppy", perk="bell", quest="buttons", profit_goal=1, seed=None),
    StoryParams(setting="harbor", pig_name="Percy", perk="ribbon", quest="shells", profit_goal=2, seed=None),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen perk and quest do not make a gentle, profitable curiosity quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld about a curious pig, a perk, and a profit quest."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--perk", choices=PERKS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--pig-name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.perk is None or c[1] == args.perk)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, perk, quest = rng.choice(sorted(combos))
    pig_name = args.pig_name or rng.choice(PIG_NAMES)
    return StoryParams(setting=setting, pig_name=pig_name, perk=perk, quest=quest, profit_goal=QUESTS[quest].profit)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.perk not in PERKS or params.quest not in QUESTS:
        raise StoryError("(Invalid StoryParams values.)")
    world = tell(SETTINGS[params.setting], PERKS[params.perk], QUESTS[params.quest], params.pig_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PERKS.items():
        lines.append(asp.fact("perk", pid))
        lines.append(asp.fact("bonus", pid, p.bonus))
        lines.append(asp.fact("cost", pid, p.cost))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("profit", qid, q.profit))
        lines.append(asp.fact("curiosity_need", qid, q.required_curiosity))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,Q) :- setting(S), perk(P), quest(Q), bonus(P,B), B >= 1, curiosity_need(Q,N), N >= 1.
profitable(Q) :- quest(Q), profit(Q, P), P >= 1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH in generate() smoke test: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, p, q in combos:
            print(f"  {s:8} {p:8} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.pig_name}: {p.perk} / {p.quest} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
