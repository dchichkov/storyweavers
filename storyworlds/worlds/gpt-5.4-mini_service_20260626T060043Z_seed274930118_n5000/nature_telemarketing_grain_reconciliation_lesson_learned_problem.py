#!/usr/bin/env python3
"""
A small fable-like storyworld about nature, telemarketing, grain, and the
reconciliation that comes from learning a better way to solve a problem.

The seed premise:
- A careful farmer keeps grain in a field-edge granary near a bright meadow.
- A telemarketer keeps calling with a pushy grain deal.
- The calls disturb the animals and stall the work.
- A wiser voice helps them reconcile, solve the problem, and learn a lesson.

The world is deliberately small, classical, and state-driven:
- meters track physical conditions like noise, scattered grain, and stored grain
- memes track feelings like worry, irritation, trust, and relief

This file follows the Storyweavers world contract:
- standalone stdlib script
- imports shared results eagerly
- lazily imports asp inside ASP helpers
- supports parser / resolve_params / generate / emit / main
- includes inline ASP_RULES and parity verification
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

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("noise", 0.0)
        self.meters.setdefault("scatter", 0.0)
        self.meters.setdefault("stored", 0.0)
        self.meters.setdefault("dryness", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("irritation", 0.0)
        self.memes.setdefault("trust", 0.0)
        self.memes.setdefault("relief", 0.0)
        self.memes.setdefault("wisdom", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    nature_detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    problem: str
    fixword: str
    kind: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "storage"
    plural: bool = False


@dataclass
class Solution:
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.noise_source: str = ""

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(
        place="the meadow",
        nature_detail="The meadow was full of clover, bees, and tall grass.",
        affords={"call", "harvest", "listen"},
    ),
    "farm": Setting(
        place="the farm edge",
        nature_detail="Near the farm edge, wind moved through the wheat and the fence hummed softly.",
        affords={"call", "harvest", "listen"},
    ),
    "riverbank": Setting(
        place="the riverbank",
        nature_detail="The riverbank had reeds, mud, and a path where birds liked to land.",
        affords={"call", "harvest", "listen"},
    ),
}

ACTIONS = {
    "telemarketing": Action(
        id="telemarketing",
        verb="make telemarketing calls",
        gerund="making telemarketing calls",
        problem="too much noise",
        fixword="quiet",
        kind="noise",
        weather="breezy",
        tags={"telemarketing", "noise"},
    ),
    "grain_shuffle": Action(
        id="grain_shuffle",
        verb="move the grain sacks",
        gerund="moving grain sacks",
        problem="grain scattered",
        fixword="sorted",
        kind="scatter",
        weather="sunny",
        tags={"grain", "problem-solving"},
    ),
    "listen_well": Action(
        id="listen_well",
        verb="listen carefully",
        gerund="listening carefully",
        problem="hurried decisions",
        fixword="thoughtful",
        kind="trust",
        weather="calm",
        tags={"lesson", "reconciliation"},
    ),
}

PRIZES = {
    "grain": Prize(
        label="grain",
        phrase="a basket of golden grain",
        type="grain",
    ),
    "sacks": Prize(
        label="sacks",
        phrase="three sturdy grain sacks",
        type="sacks",
        plural=True,
        type="sacks",
    ),
    "basket": Prize(
        label="basket",
        phrase="a woven basket for the harvest",
        type="basket",
    ),
}

SOLUTIONS = [
    Solution(
        label="a hand-painted sign",
        phrase="a hand-painted sign",
        prep="put up",
        tail="set the sign by the lane",
        guards={"noise"},
    ),
    Solution(
        label="a quiet call time",
        phrase="a quiet call time",
        prep="choose",
        tail="kept the calls for later in the day",
        guards={"noise"},
    ),
    Solution(
        label="a sorting table",
        phrase="a sorting table",
        prep="set out",
        tail="sorted the grain before it spilled again",
        guards={"scatter"},
    ),
]

HEROES = ["Mina", "Toby", "Iris", "Pip", "Lena", "Jonah"]
GUIDES = ["Grandmother", "Old Hare", "Field Mouse", "Mole", "Heron"]
TRAITS = ["kind", "curious", "patient", "thoughtful", "brave"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    hero: str
    guide: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            for prize in PRIZES:
                if action == "telemarketing" and prize in {"grain", "sacks"}:
                    combos.append((place, action, prize))
                if action == "grain_shuffle" and prize in {"grain", "sacks", "basket"}:
                    combos.append((place, action, prize))
                if action == "listen_well":
                    combos.append((place, action, prize))
    return combos


def explain_rejection(action: Action, prize: Prize) -> str:
    if action.id == "telemarketing" and prize.label == "basket":
        return "(No story: telemarketing calls do not naturally endanger a basket in this small world.)"
    return "(No story: that combination does not create a clear problem and resolution.)"


def select_solution(action: Action, prize: Prize) -> Optional[Solution]:
    if action.kind == "noise":
        return next((s for s in SOLUTIONS if "noise" in s.guards), None)
    if action.kind == "scatter" and prize.label in {"grain", "sacks"}:
        return next((s for s in SOLUTIONS if "scatter" in s.guards), None)
    return None


def _narrate_problem(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["noise"] >= THRESHOLD and e.memes["worry"] < THRESHOLD:
            e.memes["worry"] += 1
            out.append(f"The noise made {e.id} worry that the work would not get done.")
    return out


def _narrate_scatter(world: World) -> list[str]:
    out: list[str] = []
    grain = world.entities.get("grain")
    if grain and grain.meters["scatter"] >= THRESHOLD and grain.meters["stored"] < THRESHOLD:
        out.append("Some of the grain scattered into the grass.")
    return out


def _narrate_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    guide = world.get("guide")
    if hero.memes["trust"] >= THRESHOLD and guide.memes["trust"] >= THRESHOLD:
        hero.memes["relief"] += 1
        guide.memes["relief"] += 1
        out.append("They forgave the fuss and spoke gently to one another.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_narrate_problem, _narrate_scatter, _narrate_reconcile):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def intro(world: World, hero: Entity, guide: Entity) -> None:
    world.say(
        f"{hero.id} was a little {world.facts['trait']} helper who loved the green world around {hero.pronoun('possessive')} home."
    )
    world.say(
        f"One day, {hero.id} worked beside {guide.id} in {world.setting.place}, where {world.setting.nature_detail}"
    )


def set_up(world: World, hero: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"They kept {prize.phrase} ready for the day, because the {action.verb} would soon begin."
    )


def create_conflict(world: World, hero: Entity, guide: Entity, action: Action, prize: Entity) -> None:
    if action.kind == "noise":
        hero.memes["worry"] += 1
        guide.memes["irritation"] += 1
        world.say(
            f"Then a loud caller began {action.gerund}, and the ringing bounced through the grass."
        )
        world.say(
            f"{hero.id} covered {hero.pronoun('possessive')} ears, and {guide.id} frowned at the interruptions."
        )
        world.noise_source = "call"
        world.facts["problem"] = "noise"
        world.facts["lesson"] = "too much noise can trouble a peaceful place"
    else:
        prize.meters["scatter"] += 1
        hero.memes["worry"] += 1
        world.say(
            f"While they worked, the wind tipped the {prize.label} and made the grain spill into the dirt."
        )
        world.say(
            f"{hero.id} gasped, because a problem had turned a careful job into a messy one."
        )
        world.facts["problem"] = "scatter"
        world.facts["lesson"] = "small mistakes can be fixed with patience"
    propagate(world)


def offer_reconciliation(world: World, hero: Entity, guide: Entity, action: Action, prize: Entity) -> Optional[Solution]:
    sol = select_solution(action, prize)
    if sol is None:
        return None
    if action.kind == "noise":
        hero.memes["trust"] += 1
        guide.memes["trust"] += 1
        world.say(
            f"{guide.id} took a breath and suggested a kinder plan: {sol.phrase} so the calling would not frighten the birds."
        )
    else:
        hero.memes["trust"] += 1
        guide.memes["trust"] += 1
        world.say(
            f"{guide.id} did not scold. Instead, {guide.pronoun('subject')} suggested {sol.phrase} so the grain could be gathered again."
        )
    return sol


def resolve(world: World, hero: Entity, guide: Entity, action: Action, prize: Entity, sol: Solution) -> None:
    hero.memes["trust"] += 1
    guide.memes["trust"] += 1
    hero.memes["relief"] += 1
    guide.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    guide.memes["wisdom"] += 1
    world.say(
        f"{hero.id} listened, and {hero.pronoun('subject')} agreed to the better plan."
    )
    if action.kind == "noise":
        world.say(
            f"They {sol.prep} {sol.label} and {sol.tail}. The meadow grew quiet again, and the robins sang over the field."
        )
    else:
        prize.meters["scatter"] = 0.0
        prize.meters["stored"] += 1
        world.say(
            f"They {sol.prep} {sol.label} and {sol.tail}. Soon the grain was gathered back into the basket, neat and safe."
        )
    world.say(
        f"By the end, {hero.id} and {guide.id} smiled together, because they had solved the problem without hurting the peace of the place."
    )
    world.facts["solution"] = sol.label
    world.facts["resolved"] = True


def lesson(world: World, hero: Entity, guide: Entity, action: Action) -> None:
    world.say(
        f"{hero.id} learned that a good helper fixes trouble with calm words, careful hands, and respect for the living world."
    )
    world.say(
        f"{guide.id} learned that even a noisy problem can become a gentle lesson when someone is willing to listen."
    )


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, guide_name: str, trait: str) -> World:
    world = World(setting)
    world.facts["trait"] = trait
    world.facts["action"] = action
    world.facts["prize_cfg"] = prize_cfg

    hero = world.add(Entity(id="hero", kind="character", type="child", label=hero_name))
    guide = world.add(Entity(id="guide", kind="character", type="adult", label=guide_name))
    prize = world.add(Entity(id="grain", kind="thing", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))

    intro(world, hero, guide)
    world.para()
    set_up(world, hero, prize, action)
    create_conflict(world, hero, guide, action, prize)
    world.para()
    sol = offer_reconciliation(world, hero, guide, action, prize)
    if sol:
        resolve(world, hero, guide, action, prize, sol)
    lesson(world, hero, guide, action)
    world.facts.update(hero=hero, guide=guide, prize=prize, setting=setting, action=action, solution=sol)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable about nature, telemarketing, and grain, with a problem and a gentle reconciliation.',
        f"Tell a child-friendly story where {f['hero'].label} and {f['guide'].label} solve a {f['action'].kind} problem in {world.setting.place}.",
        f"Write a simple fable that ends with a lesson learned about {f['action'].problem}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    action: Action = f["action"]
    prize: Entity = f["prize"]
    setting: Setting = f["setting"]

    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label} and {guide.label} in {setting.place}.",
        ),
        QAItem(
            question=f"What problem came up in the story?",
            answer=f"The problem was {action.problem}, which made the peaceful work harder for everyone.",
        ),
        QAItem(
            question=f"What were they trying to keep safe or in order?",
            answer=f"They were trying to keep {prize.phrase} safe and the work in order.",
        ),
    ]
    if f.get("resolved"):
        sol = f["solution"]
        qa.append(
            QAItem(
                question="How did they fix the problem?",
                answer=f"They fixed it by choosing {sol}, which matched the problem instead of making it worse.",
            )
        )
        qa.append(
            QAItem(
                question="What lesson did the story teach?",
                answer=f"The lesson was that {world.facts['lesson']}, and that calm kindness can solve a problem better than anger.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "nature": [
        (
            "What is nature?",
            "Nature is the world of living things and places outside, like trees, grass, birds, water, and soil.",
        )
    ],
    "telemarketing": [
        (
            "What is telemarketing?",
            "Telemarketing is when someone makes sales calls to people by phone to tell them about a product or service.",
        )
    ],
    "grain": [
        (
            "What is grain?",
            "Grain is a small food crop, like wheat or rice, that people and animals can eat.",
        )
    ],
    "problem-solving": [
        (
            "What does problem-solving mean?",
            "Problem-solving means finding a good way to fix trouble instead of just arguing about it.",
        )
    ],
    "lesson": [
        (
            "What is a lesson learned?",
            "A lesson learned is a helpful idea you remember after something happens, so you can do better next time.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation means making peace again after people have disagreed or been upset.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"nature", "telemarketing", "grain", "problem-solving", "lesson", "reconciliation"}
    out: list[QAItem] = []
    for tag in tags:
        for q, a in WORLD_KNOWLEDGE.get(tag, []):
            out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
problem(noise) :- action(telemarketing).
problem(scatter) :- action(grain_shuffle).

valid(Place, Action, Prize) :- affords(Place, Action), action(Action), prize(Prize),
                               Action = telemarketing, Prize = grain.
valid(Place, Action, Prize) :- affords(Place, Action), action(Action), prize(Prize),
                               Action = grain_shuffle.

lesson_learned(Place) :- valid(Place, Action, Prize), action(Action), prize(Prize).
reconciliation_possible(Action) :- action(Action), Action = telemarketing.
reconciliation_possible(Action) :- action(Action), Action = grain_shuffle.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("kind", aid, action.kind))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation / emit
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about nature, telemarketing, grain, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.prize:
        action = ACTIONS[args.action]
        prize = PRIZES[args.prize]
        if action.id == "telemarketing" and prize.label not in {"grain", "sacks"}:
            raise StoryError(explain_rejection(action, prize))
        if action.id == "grain_shuffle" and prize.label not in {"grain", "sacks", "basket"}:
            raise StoryError(explain_rejection(action, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        hero=args.name or rng.choice(HEROES),
        guide=args.guide or rng.choice(GUIDES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        PRIZES[params.prize],
        params.hero,
        params.guide,
        params.trait,
    )
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
    StoryParams(place="meadow", action="telemarketing", prize="grain", hero="Mina", guide="Old Hare", trait="thoughtful"),
    StoryParams(place="farm", action="grain_shuffle", prize="sacks", hero="Toby", guide="Grandmother", trait="patient"),
    StoryParams(place="riverbank", action="telemarketing", prize="grain", hero="Iris", guide="Field Mouse", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
