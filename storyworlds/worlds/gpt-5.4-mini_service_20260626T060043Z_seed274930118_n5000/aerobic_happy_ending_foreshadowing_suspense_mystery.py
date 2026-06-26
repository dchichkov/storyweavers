#!/usr/bin/env python3
"""
storyworlds/worlds/aerobic_happy_ending_foreshadowing_suspense_mystery.py
=========================================================================

A small storyworld about a child, an aerobic routine, and a gentle mystery.

Premise:
- A child wants to do an aerobic routine in a place that supports it.
- A useful item is missing or at risk.
- Small clues create foreshadowing and suspense.
- The child investigates, finds the solution, and ends happily.

The world is intentionally tiny and constraint-checked:
- only a few plausible settings, activities, and prized items are allowed
- the mystery must be solvable by the built-in world logic
- invalid explicit choices raise StoryError with a clear reason
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
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
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    clue: str
    sound: str
    mess: str
    zone: set[str]
    keyword: str = "aerobic"


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Hint:
    text: str
    reveal: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clues: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.clues = list(self.clues)
        return clone


SETTINGS = {
    "gym": Setting(place="the gym", indoor=True, affords={"aerobic"}),
    "studio": Setting(place="the dance studio", indoor=True, affords={"aerobic"}),
    "living_room": Setting(place="the living room", indoor=True, affords={"aerobic"}),
}

ACTIVITIES = {
    "aerobic": Activity(
        id="aerobic",
        verb="do an aerobic routine",
        gerund="doing an aerobic routine",
        clue="a little bounce-bounce pattern",
        sound="tap-tap-clap",
        mess="sweaty",
        zone={"feet", "torso"},
        keyword="aerobic",
    ),
    "jumping": Activity(
        id="jumping",
        verb="do jumping jacks",
        gerund="doing jumping jacks",
        clue="arms that rose and fell like wings",
        sound="pat-pat-whoosh",
        mess="sweaty",
        zone={"feet", "torso"},
        keyword="aerobic",
    ),
    "steps": Activity(
        id="steps",
        verb="practice step-taps",
        gerund="practicing step-taps",
        clue="a neat side-step and tap",
        sound="tap-tap-step",
        mess="sweaty",
        zone={"feet", "torso"},
        keyword="aerobic",
    ),
}

PRIZES = {
    "headband": Prize(
        label="headband",
        phrase="a bright red headband",
        type="headband",
        region="torso",
    ),
    "sneakers": Prize(
        label="sneakers",
        phrase="a pair of springy sneakers",
        type="sneakers",
        region="feet",
        genders={"girl", "boy"},
    ),
    "water_bottle": Prize(
        label="water bottle",
        phrase="a blue water bottle with stars",
        type="bottle",
        region="hand",
    ),
}

HELPERS = {
    "toy_box": Hint(text="The toy box sat by the wall.", reveal="under a towel"),
    "bench": Hint(text="The bench looked neat and empty.", reveal="behind the bench"),
    "mat": Hint(text="A folded mat made one corner look puffier than the others.", reveal="inside the mat pile"),
}

NAMES = {
    "girl": ["Maya", "Nina", "Luna", "Pia", "Zoe", "Ivy"],
    "boy": ["Leo", "Eli", "Noah", "Finn", "Theo", "Max"],
}
TRAITS = ["curious", "brave", "cheerful", "patient", "careful"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.region == "hand"


def select_hint(activity: Activity, prize: Prize) -> Optional[Hint]:
    if prize.label == "headband" and activity.id in {"aerobic", "steps"}:
        return HELPERS["mat"]
    if prize.label == "sneakers" and activity.id in {"aerobic", "jumping"}:
        return HELPERS["bench"]
    if prize.label == "water bottle":
        return HELPERS["toy_box"]
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: this mystery only works when the {prize.label} can matter "
        f"during {activity.gerund}. Try another valid combo.)"
    )


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small aerobic mystery with a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(ACTIVITIES[act], prize):
                    combos.append((place, act, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if args.activity and args.prize:
        if not prize_at_risk(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(NAMES[gender])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, trait=trait)


def _do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0) + 1
    hero.memes["energy"] = hero.memes.get("energy", 0) + 1


def predict_missing(world: World, hero: Entity, prize: Entity, activity: Activity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity)
    return bool(sim.get(prize.id).hidden_in)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={}))
    prize = world.add(
        Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id)
    )
    helper = world.add(Entity(id="helper", type="thing", label="the clue", phrase="a clue"))
    hint = select_hint(activity, prize_cfg)
    if hint:
        helper.hidden_in = hint.reveal
    world.facts.update(hero=hero, prize=prize, activity=activity, setting=setting, hint=hint)

    world.say(
        f"{hero.id} was a {trait} little {gender} who loved clues and counted steps softly."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {activity.clue} made {activity.keyword} feel magical."
    )
    world.say(
        f"Before the music started, {hero.id}'s {prize.label} was missing."
    )
    if hint:
        world.say(hint.text)
    world.para()

    world.say(
        f"At {setting.place}, the room felt quiet, but the silence made every tiny sound suspicious."
    )
    world.say(
        f"{hero.id} listened for a {activity.sound} and looked where a small thing might hide."
    )
    if predict_missing(world, hero, prize, activity):
        prize.hidden_in = hint.reveal if hint else "somewhere nearby"
        world.say(
            f"That was the mystery: the {prize.label} had been tucked {prize.hidden_in} all along."
        )

    world.para()
    hero.memes["suspense"] = 1
    world.say(
        f"{hero.id} peeked, lifted, and checked one careful place after another until the answer appeared."
    )
    prize.carried_by = hero.id
    hero.memes["joy"] = 1
    hero.memes["worry"] = 0
    world.say(
        f"Then {hero.id} smiled, wore the {prize.label}, and began {activity.gerund} with a bright {activity.sound} rhythm."
    )
    world.say(
        f"The room filled with happy feet, and the little mystery ended the nicest way possible."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story about "{f["activity"].keyword}" with a happy ending.',
        f"Tell a short story in which {f['hero'].id} searches for a missing {f['prize'].label} before an aerobic routine.",
        f"Write a suspenseful but gentle story where clues help {f['hero'].id} get ready to {f['activity'].verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, activity, setting = f["hero"], f["prize"], f["activity"], f["setting"]
    hint = f.get("hint")
    ans_hint = hint.text if hint else "There was a small clue."
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb} at {setting.place}.",
        ),
        QAItem(
            question=f"What was missing before the music started?",
            answer=f"The {prize.label} was missing before the music started.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=ans_hint,
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {hero.id} found the {prize.label} and began {activity.gerund}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does aerobic mean?",
            answer="Aerobic means active exercise that gets your body moving and helps your heart work.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="Why can suspense make a story exciting?",
            answer="Suspense makes a story exciting because you wonder what will happen next.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid_story(P,A,R) :- place(P), activity(A), prize(R), afford(P,A), at_risk(A,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("at_risk", "aerobic", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="gym", activity="aerobic", prize="headband", name="Maya", gender="girl", trait="curious"),
    StoryParams(place="studio", activity="jumping", prize="sneakers", name="Leo", gender="boy", trait="careful"),
    StoryParams(place="living_room", activity="steps", prize="water_bottle", name="Ivy", gender="girl", trait="brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
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
            print("  ", t)
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
