#!/usr/bin/env python3
"""
storyworlds/worlds/lush_moral_value_foreshadowing_twist_slice_of.py
====================================================================

A tiny slice-of-life storyworld about a lush garden, a small moral choice,
gentle foreshadowing, and a soft twist.

Seed tale:
---
A child helps in a lush garden with a parent or caretaker. The child thinks a
tall plant is a weed and wants to cut it down or pull it out. The parent notices
small clues first: a ribbon on the stake, a label half-hidden under leaves, and
new buds tucked inside the green. The parent asks the child to wait and look
closer. The twist is that the "messy" plant is actually something precious and
useful, like a climbing vegetable or a surprise gift for someone else. The child
chooses patience and care, learns that looking closely matters, and helps tend
the garden instead of ruining it.

Story model:
---
- Physical meters: thirst, growth, bruised, neatness, sunlight, rootedness.
- Emotional memes: curiosity, impatience, worry, pride, relief, kindness.

The prose is intentionally slice-of-life and authored from the evolving world
state rather than as a static paragraph with swapped names.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the lush garden"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    risk_tag: str
    keyword: str = "lush"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    kind_hint: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Hint:
    label: str
    clue: str
    payoff: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "garden": Setting(place="the lush garden", indoor=False, affords={"inspect", "water", "trim"}),
    "courtyard": Setting(place="the lush courtyard", indoor=False, affords={"inspect", "water"}),
    "greenhouse": Setting(place="the lush greenhouse", indoor=True, affords={"inspect", "water", "trim"}),
}

ACTIVITIES = {
    "inspect": Activity(
        id="inspect",
        verb="look closely at the plant",
        gerund="looking closely at the plant",
        rush="reach for the stems",
        mess="creased",
        soil="creased and bent",
        risk_tag="tender",
        tags={"look", "clue"},
    ),
    "water": Activity(
        id="water",
        verb="water the plant",
        gerund="watering the plant",
        rush="tip the watering can too fast",
        mess="splashed",
        soil="splashed and muddy",
        risk_tag="dry",
        tags={"water", "lush"},
    ),
    "trim": Activity(
        id="trim",
        verb="trim the tall stem",
        gerund="trimming the tall stem",
        rush="snip the wrong branch",
        mess="cut",
        soil="cut too short",
        risk_tag="hidden",
        tags={"trim", "twist"},
    ),
}

PRIZES = {
    "vine": Prize(
        label="vine",
        phrase="a tall leafy vine",
        type="vine",
        kind_hint="plant",
        genders={"girl", "boy"},
    ),
    "sprout": Prize(
        label="sprout",
        phrase="a small potted sprout",
        type="sprout",
        kind_hint="plant",
        genders={"girl", "boy"},
    ),
    "basket": Prize(
        label="basket",
        phrase="a little woven basket",
        type="basket",
        kind_hint="basket",
        genders={"girl", "boy"},
    ),
}

HINTS = {
    "ribbon": Hint(
        label="ribbon",
        clue="a blue ribbon tied around the stake",
        payoff="The ribbon was not decoration; it marked the plant that needed careful hands.",
    ),
    "tag": Hint(
        label="tag",
        clue="a paper tag tucked under the leaves",
        payoff="The tag showed that the plant was a special one, meant to be kept safe.",
    ),
    "buds": Hint(
        label="buds",
        clue="tiny buds hiding under the leaves",
        payoff="The buds meant the plant was alive and growing, not just a messy weed.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Theo", "Max", "Sam"]
TRAITS = ["curious", "gentle", "stubborn", "careful", "playful", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    if prize.kind_hint == "plant":
        return activity.id in {"trim", "inspect", "water"}
    return activity.id in {"trim", "inspect"}


def select_fix(activity: Activity, prize: Prize) -> bool:
    return prize.kind_hint == "plant" and activity.id in {"inspect", "water"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_fix(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not create a believable garden lesson for "
        f"{prize.label}. The twist needs a plant that can actually be saved by "
        f"looking closer or watering it.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this prize is not restricted here; try --gender {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life garden storyworld with moral value, foreshadowing, and a twist."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_fix(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def predict(world: World, hero: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    p = sim.get(prize.id)
    if activity.id == "trim":
        p.meters["bruised"] = p.meters.get("bruised", 0) + 1
        p.meters["neatness"] = p.meters.get("neatness", 0) - 1
    elif activity.id == "water":
        p.meters["thirst"] = max(0.0, p.meters.get("thirst", 0) - 1.0)
        p.meters["growth"] = p.meters.get("growth", 0) + 1
    else:
        p.meters["neatness"] = p.meters.get("neatness", 0) + 0.1
    return {
        "hurt": p.meters.get("bruised", 0) >= THRESHOLD,
        "saved": activity.id in {"inspect", "water"},
    }


def _apply_activity(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    if activity.id == "water":
        prize.meters["thirst"] = max(0.0, prize.meters.get("thirst", 1.0) - 1.0)
        prize.meters["growth"] = prize.meters.get("growth", 0) + 1.0
        hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1.0
    elif activity.id == "inspect":
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1.0
        prize.meters["neatness"] = prize.meters.get("neatness", 0) + 0.2
    elif activity.id == "trim":
        prize.meters["bruised"] = prize.meters.get("bruised", 0) + 1.0
        prize.meters["neatness"] = prize.meters.get("neatness", 0) - 0.5


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, parent_type: str,
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"neatness": 0.0},
        memes={"curiosity": 0.0, "impatience": 0.0, "kindness": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        meters={"thirst": 1.0, "growth": 0.2, "neatness": 0.3, "bruised": 0.0},
        tags={"lush", "plant"},
    ))
    hint = world.add(Entity(id="Hint", type="hint", label="garden clue"))

    trait = next((t for t in (hero_traits or []) if t != "little"), "curious")
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, hint=hint, trait=trait)

    world.say(f"{hero.id} was a little {trait} {hero.type} who loved the lush garden.")
    world.say(f"{hero.id} liked the soft leaves, the damp soil, and the quiet way the garden smelled after water.")
    world.say(f"That morning, {hero.id} noticed {prize.label} standing a little too tall and a little too wild.")

    clue = HINTS["ribbon"]
    world.say(f"There was {clue.clue}, and the stem had a few tiny buds hidden in the green.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label_word if hasattr(parent, 'label_word') else 'parent'} watched closely.")

    world.say(f'"Wait," said {parent.label_word if hasattr(parent, "label_word") else "the parent"}. "Look again before you decide."')
    world.say(f"{hero.id} leaned in and saw {HINTS['tag'].clue}.")

    if activity.id == "trim":
        world.say(f"{hero.id} almost rushed to {activity.rush}, but {parent.label_word if hasattr(parent, 'label_word') else 'the parent'} held up a calm hand.")
        world.say(f"The little tag showed that {prize.label} was not a weed at all.")
        world.say(f"It was a special plant for the family, and it needed care, not a quick snip.")
        _apply_activity(world, hero, prize, ACTIVITIES["inspect"])
        hero.memes["impatience"] = max(0.0, hero.memes["impatience"] - 0.5)
        hero.memes["curiosity"] += 1.0
        hero.memes["relief"] += 1.0
        hero.memes["pride"] += 1.0
        world.say(f"{hero.id} felt a little embarrassed, then relieved, because slowing down had kept the plant safe.")
        world.say(f"Together they watered it gently, and the leaves stood up brighter in the warm light.")
        world.say(f"By the end, {hero.id} was smiling at the proof: the lush plant was still there, growing stronger.")
    else:
        world.say(f"{hero.id} did not rush to pull it. Instead, {hero.id} listened and looked.")
        world.say(HINTS["buds"].payoff)
        world.say(f"So {hero.id} chose to {activity.verb}, which was kinder and wiser than tearing it up.")
        _apply_activity(world, hero, prize, activity)
        hero.memes["kindness"] += 1.0
        hero.memes["pride"] += 1.0
        hero.memes["relief"] += 1.0
        world.say(f"The twist was simple: the messy-looking plant was the one that needed help most.")
        world.say(f"When it was watered, the leaves shone, and the whole garden seemed to breathe easier.")

    if prize.meters.get("growth", 0) >= THRESHOLD:
        world.say(f"Later, {hero.id} noticed a new green tip where the old worry had been.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short slice-of-life story for a child about "{world.setting.place}", a garden clue, and a gentle twist.',
        f"Tell a warm story where {hero.id} wants to {act.verb} but learns to look closely before acting.",
        f"Write a story with a moral value about patience and care, set in {world.setting.place}, using the word 'lush'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the garden before the twist?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What clue first made the plant look important instead of like a weed?",
            answer=f"The first clue was {HINTS['ribbon'].clue}, and then {HINTS['tag'].clue}.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end of the story?",
            answer="The child learned to slow down, look closely, and choose care instead of tearing something up too quickly.",
        ),
        QAItem(
            question=f"Why was the final choice a good moral choice?",
            answer="Because patience and kindness kept the plant safe and helped the garden grow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does lush mean?",
            answer="Lush means full, green, and healthy-looking, like a garden with plenty of growing plants.",
        ),
        QAItem(
            question="Why should you look closely before pulling up a plant?",
            answer="Because some plants that look messy at first are actually important, and pulling them too soon can hurt them.",
        ),
        QAItem(
            question="What does a watering can do?",
            answer="A watering can carries water so you can pour it gently onto plants that need a drink.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def valid_story_qas(world: World) -> StorySample:
    return StorySample(
        params=world.facts["params"],
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.parent,
        [params.trait, "little"],
    )
    world.facts["params"] = params
    return valid_story_qas(world)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), risky(A,P).
has_fix(A,P) :- prize_at_risk(A,P), can_fix(A,P).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tagged", aid, t))
        if a.id in {"trim", "inspect"}:
            lines.append(asp.fact("risky", aid, "plant"))
            lines.append(asp.fact("can_fix", aid, "plant"))
        if a.id == "water":
            lines.append(asp.fact("risky", aid, "plant"))
            lines.append(asp.fact("can_fix", aid, "plant"))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


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
    StoryParams(place="garden", activity="inspect", prize="vine", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="courtyard", activity="water", prize="sprout", name="Leo", gender="boy", parent="father", trait="patient"),
    StoryParams(place="greenhouse", activity="trim", prize="vine", name="Nora", gender="girl", parent="mother", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
