#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chowmein_decimal_quest_twist_fable.py
======================================================================

A standalone storyworld for a tiny fable-like quest: someone sets out to fetch
ingredients for chowmein, gets tripped up by a decimal mix-up, and learns a
small practical lesson through a twist.

The world is built from typed entities with physical ``meters`` and emotional
``memes``. State changes drive narration; the prose is not a frozen template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

QUEST_MIN_CONFIDENCE = 2
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    carries: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "goat"}
        male = {"boy", "father", "dad", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    shelter: str
    path: str
    quest_need: str
    twist_view: str


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    kind: str
    weight: float
    tags: set[str] = field(default_factory=set)


@dataclass
class DecimalProblem:
    id: str
    amount: float
    display: str
    consequence: str
    fix_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistRule:
    id: str
    trigger: str
    reveal: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hungry(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["hungry"] < THRESHOLD:
            continue
        sig = ("hungry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["resolve"] += 1
        out.append(f"{e.id} felt more determined to finish the quest.")
    return out


def _r_decimal_spill(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["confused"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "market" in world.entities:
            world.get("market").meters["chaos"] += 1
        e.memes["worry"] += 1
        out.append("__twist__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("hungry", "social", _r_hungry),
    Rule("decimal_spill", "social", _r_decimal_spill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: Setting, quest: QuestItem, problem: DecimalProblem) -> bool:
    return quest.kind == "food" and "decimal" in problem.tags and setting.id in SETTINGS


def quest_at_risk(setting: Setting, quest: QuestItem) -> bool:
    return quest.weight >= 1.0 and setting.id in SETTINGS


def outcome_power(s: Solution, problem: DecimalProblem) -> bool:
    return s.power >= 1 if problem.amount >= 0.5 else True


def predict_mixup(world: World, hero: Entity, problem: DecimalProblem) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["confused"] += 1
    propagate(sim, narrate=False)
    return {
        "chaos": sim.get("market").meters["chaos"] if "market" in sim.entities else 0,
        "worry": sim.get(hero.id).memes["worry"],
    }


def start(world: World, hero: Entity, elder: Entity, setting: Setting, quest: QuestItem) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In a quiet {setting.mood} village, {hero.id} and {elder.id} lived by the little {setting.place}."
        f" They kept a tiny bowl for sharing chowmein and a neat notebook for counting."
    )
    world.say(
        f"{hero.id} loved the taste of chowmein and the way a full bowl could make a hungry day feel kind."
    )
    world.say(
        f"{hero.id} dreamed up a quest: to bring home {quest.phrase} for supper before the sun went down."
    )


def set_out(world: World, hero: Entity, elder: Entity, quest: QuestItem, setting: Setting) -> None:
    hero.meters["hungry"] += 1
    world.say(
        f"At dawn, {hero.id} set off down {setting.path}, carrying a basket and thinking of the warm noodles ahead."
    )
    world.say(
        f"{elder.id} called after {hero.id}, reminding {hero.pronoun('object')} to count carefully and keep the basket steady."
    )


def warn_decimal(world: World, elder: Entity, hero: Entity, problem: DecimalProblem) -> None:
    pred = predict_mixup(world, hero, problem)
    hero.meters["confused"] += 1
    world.facts["pred"] = pred
    world.say(
        f"{elder.id} pointed at the handwritten note. \"That dot is a decimal,\" {elder.pronoun()} said."
        f" \"If you read it wrong, {problem.consequence}.\""
    )
    if pred["chaos"] >= 1:
        world.say(
            f"{elder.id} frowned a little, because the market could get messy if the counting went wrong."
        )


def twist(world: World, hero: Entity, problem: DecimalProblem, rule: TwistRule) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"But when {hero.id} reached the stall, the sign had a twist: {rule.reveal}."
    )
    world.say(
        f"The seller had written the price in a hurry, and the decimal point made the number look smaller than it was."
    )
    world.say(rule.consequence)


def choose_fix(world: World, elder: Entity, solution: Solution, problem: DecimalProblem) -> None:
    body = solution.text
    world.say(
        f"{elder.id} took a breath, then {body}."
    )
    if solution.power >= 1:
        problem.amount = 0.0
        world.get("market").meters["chaos"] = 0.0
        world.say(
            f"The mistaken number was set right, and the counter became calm again."
        )
    else:
        world.say(
            f"It helped a little, but not enough to settle the puzzle."
        )


def end(world: World, hero: Entity, elder: Entity, quest: QuestItem, setting: Setting) -> None:
    hero.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"By evening, they carried home {quest.phrase}, and the smell of chowmein filled the little house."
    )
    world.say(
        f"{hero.id} learned that a tiny decimal point can change a big plan, so careful counting matters."
    )
    world.say(
        f"That night, the village was peaceful, and the bowl of chowmein disappeared happily between them."
    )


def tell(setting: Setting, quest: QuestItem, problem: DecimalProblem, twist_rule: TwistRule,
         solution: Solution, hero_name: str = "Mina", hero_type: str = "girl",
         elder_name: str = "Grandma", elder_type: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="quester"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="guide"))
    market = world.add(Entity(id="market", type="place", label="the market"))
    world.facts["setting"] = setting
    world.facts["quest"] = quest
    world.facts["problem"] = problem
    world.facts["twist"] = twist_rule
    world.facts["solution"] = solution
    world.facts["market"] = market
    start(world, hero, elder, setting, quest)
    world.para()
    set_out(world, hero, elder, quest, setting)
    warn_decimal(world, elder, hero, problem)
    world.para()
    twist(world, hero, problem, twist_rule)
    choose_fix(world, elder, solution, problem)
    world.para()
    end(world, hero, elder, quest, setting)
    world.facts.update(
        hero=hero,
        elder=elder,
        resolved=problem.amount == 0.0,
        twist_seen=True,
    )
    return world


SETTINGS = {
    "village": Setting(
        id="village",
        place="market square",
        mood="sunlit",
        shelter="little house",
        path="the stone path",
        quest_need="meal",
        twist_view="bright awning",
    ),
    "harbor": Setting(
        id="harbor",
        place="harbor lane",
        mood="windy",
        shelter="tea shop",
        path="the dock road",
        quest_need="supper",
        twist_view="salt-blue sky",
    ),
}

QUESTS = {
    "chowmein": QuestItem(
        id="chowmein",
        label="chowmein",
        phrase="fresh vegetables for chowmein",
        kind="food",
        weight=1.0,
        tags={"chowmein", "food"},
    ),
    "noodles": QuestItem(
        id="noodles",
        label="noodles",
        phrase="golden noodles for chowmein",
        kind="food",
        weight=1.0,
        tags={"chowmein", "food"},
    ),
}

PROBLEMS = {
    "decimal": DecimalProblem(
        id="decimal",
        amount=0.5,
        display="1.5",
        consequence="the stallkeeper would give half as much by mistake",
        fix_text="read the decimal aloud and count again",
        tags={"decimal"},
    ),
    "decimal_tangle": DecimalProblem(
        id="decimal_tangle",
        amount=1.5,
        display="2.5",
        consequence="the bill would be too large if nobody checked it",
        fix_text="point to the dot and tally each coin slowly",
        tags={"decimal"},
    ),
}

TWISTS = {
    "market_misread": TwistRule(
        id="market_misread",
        trigger="stall",
        reveal="the price tag was wet and the decimal line looked like a tiny worm",
        consequence="The seller chuckled and wiped the sign clean, so the real price could be read at last.",
    ),
    "baker_note": TwistRule(
        id="baker_note",
        trigger="note",
        reveal="the baker had wrapped the noodles in a note with a crooked decimal",
        consequence="Once they checked the note together, the numbers made sense again.",
    ),
}

SOLUTIONS = {
    "count_again": Solution(
        id="count_again",
        sense=3,
        power=2,
        text="pointed to the decimal dot, counted the coins one by one, and asked the seller to read it again",
        fail="counted too quickly and missed the dot",
        qa_text="pointed to the decimal dot and counted again",
    ),
    "ask_guide": Solution(
        id="ask_guide",
        sense=3,
        power=2,
        text="asked the guide to read the sign aloud and compare it with the basket",
        fail="asked, but nobody compared the numbers carefully enough",
        qa_text="asked for help and compared the numbers carefully",
    ),
    "ignore": Solution(
        id="ignore",
        sense=1,
        power=0,
        text="ignored the sign and hoped the total would work itself out",
        fail="ignored the sign and hoped the total would work itself out",
        qa_text="ignored the decimal mistake",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Pia", "Tara", "Lulu"]
BOY_NAMES = ["Ben", "Omar", "Theo", "Ravi", "Milo", "Finn"]
ELDER_NAMES = ["Grandma", "Grandpa", "Auntie", "Uncle"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    problem: str
    twist: str
    solution: str
    hero: str
    hero_type: str
    elder: str
    elder_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for pid, problem in PROBLEMS.items():
                for tid, twist in TWISTS.items():
                    for sol in SOLUTIONS.values():
                        if reasonableness_gate(setting, quest, problem) and sol.sense >= QUEST_MIN_CONFIDENCE:
                            combos.append((sid, qid, pid, tid, sol.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like quest about chowmein and a decimal twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["woman", "man"])
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
    if args.solution and SOLUTIONS[args.solution].sense < QUEST_MIN_CONFIDENCE:
        raise StoryError("This solution is too weak for a fable-style story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.problem is None or c[2] == args.problem)
              and (args.twist is None or c[3] == args.twist)
              and (args.solution is None or c[4] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, problem, twist, solution = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["woman", "man"])
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(
        setting=setting, quest=quest, problem=problem, twist=twist, solution=solution,
        hero=hero, hero_type=hero_type, elder=elder, elder_type=elder_type
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable for children that includes the words chowmein and decimal.",
        f"Tell a quest story where {f['hero'].id} goes to fetch {f['quest'].phrase} and learns why a decimal point matters.",
        f"Write a gentle twist story with chowmein, a decimal mistake, and a wise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    quest = f["quest"]
    problem = f["problem"]
    twist = f["twist"]
    solution = f["solution"]
    return [
        QAItem(
            question="What was the hero trying to bring home?",
            answer=f"{hero.id} was trying to bring home {quest.phrase}. It was the heart of the supper quest.",
        ),
        QAItem(
            question="What went wrong with the price note?",
            answer=f"The decimal point made the sign easy to misread, so the number looked smaller or stranger than it really was. That was the twist that could have caused trouble.",
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"{elder.id} and {hero.id} used a careful fix: {solution.qa_text}. That set the numbers right and kept the quest peaceful.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chowmein?",
            answer="Chowmein is a noodle dish with vegetables or meat, cooked so the noodles are warm and tasty.",
        ),
        QAItem(
            question="What is a decimal point?",
            answer="A decimal point is a dot used in numbers to show parts of a whole, like 1.5.",
        ),
        QAItem(
            question="Why should someone count carefully when money is involved?",
            answer="Because a tiny number mark can change the total a lot. Careful counting helps people avoid mistakes.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("decimal_amount", pid, int(p.amount * 10)))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for sol in SOLUTIONS.values():
        lines.append(asp.fact("solution", sol.id))
        lines.append(asp.fact("sense", sol.id, sol.sense))
        lines.append(asp.fact("power", sol.id, sol.power))
    lines.append(asp.fact("sense_min", QUEST_MIN_CONFIDENCE))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,P,T,Sol) :- setting(S), quest(Q), problem(P), twist(T), solution(Sol),
                      sense(Sol,Sen), sense_min(M), Sen >= M.
#show valid/5.
"""


def asp_program(extra: str = "", show: str = "#show valid/5.") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP matches Python valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("only in ASP:", sorted(a - p))
        print("only in Python:", sorted(p - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    quest = QUESTS.get(params.quest)
    problem = PROBLEMS.get(params.problem)
    twist = TWISTS.get(params.twist)
    solution = SOLUTIONS.get(params.solution)
    if not all([setting, quest, problem, twist, solution]):
        raise StoryError("Invalid params: missing lookup table entry.")
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="quester"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_type, role="guide"))
    world.add(Entity(id="market", type="place", label="the market"))
    world.facts.update(setting=setting, quest=quest, problem=problem, twist=twist, solution=solution)
    start(world, hero, elder, setting, quest)
    world.para()
    set_out(world, hero, elder, quest, setting)
    warn_decimal(world, elder, hero, problem)
    world.para()
    twist(world, hero, problem, twist)
    choose_fix(world, elder, solution, problem)
    world.para()
    end(world, hero, elder, quest, setting)
    world.facts.update(hero=hero, elder=elder, resolved=True)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="village", quest="chowmein", problem="decimal", twist="market_misread", solution="count_again",
                hero="Mina", hero_type="girl", elder="Grandma", elder_type="woman"),
    StoryParams(setting="harbor", quest="noodles", problem="decimal_tangle", twist="baker_note", solution="ask_guide",
                hero="Theo", hero_type="boy", elder="Uncle", elder_type="man"),
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
        for row in combos:
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
