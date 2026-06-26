#!/usr/bin/env python3
"""
storyworlds/worlds/arithmetic_philosophy_transformation_fable.py
================================================================

A small fable-like story world about arithmetic, philosophy, and transformation.

Seed tale:
---
A young badger loved counting everything in the orchard. She counted apples,
stones, raindrops, and even the number of steps between trees. But she kept
feeling uneasy, because numbers told her how many things there were, not what
they meant.

One day, an old tortoise asked her a strange question: "If you have three apples
and you share one, are you poorer or kinder?" The badger thought and thought.
She counted again, then looked at her friend. At last she gave away two apples,
and the orchard felt warmer. She realized arithmetic could measure a world, but
philosophy could transform how she lived in it.

The story world tracks a child-friendly transformation:
- counting can become hoarding or care,
- a wise question can change a character's mind,
- sharing transforms a lonely scene into a generous one.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "badger"}
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
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    action_noun: str
    measure: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Guide:
    id: str
    label: str
    question: str
    reply: str
    transform: str


class World:
    def __init__(self, setting: Setting) -> None:
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_lonely(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("hoard", 0) >= THRESHOLD and hero.memes.get("wisdom", 0) < THRESHOLD:
        sig = ("lonely",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["lonely"] = hero.memes.get("lonely", 0) + 1
        out.append("The more the hero kept, the smaller the orchard felt.")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    guide = world.get("guide")
    prize = world.get("prize")
    if hero.memes.get("wisdom", 0) >= THRESHOLD and hero.memes.get("sharing", 0) >= THRESHOLD:
        sig = ("transform",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        prize.meters["shared"] = 1
        hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
        out.append(f"{guide.label}'s question transformed {hero.id}'s idea of the {prize.label}.")
    return out


CAUSAL_RULES = [Rule("lonely", _r_lonely), Rule("transform", _r_transform)]


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


def count_thought(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["arithmetic"] = hero.memes.get("arithmetic", 0) + 1
    world.say(
        f"{hero.id} loved arithmetic and counted {prize.phrase} one by one, "
        f"as if numbers could hold the whole world."
    )


def question_thought(world: World, guide: Entity, hero: Entity, prize: Entity, act: Activity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"Then {guide.label} asked, \"If you have {prize.phrase}, and you {act.verb}, "
        f"what changes besides the number?\""
    )


def hesitate(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(
        f"{hero.id} looked down at {prize.phrase} and frowned, because the answer felt "
        f"too big for simple counting."
    )


def share(world: World, hero: Entity, guide: Entity, prize: Entity) -> None:
    hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
    hero.meters["prize_count"] = max(0, hero.meters.get("prize_count", 0) - 2)
    world.say(
        f"At last, {hero.id} gave {guide.label} two {prize.label} and kept one for later."
    )
    propagate(world, narrate=False)


def resolution(world: World, hero: Entity, guide: Entity, prize: Entity) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    world.say(
        f"The orchard seemed warmer after that, and {hero.id} smiled because the "
        f"count had changed, but so had {hero.pronoun('possessive')} heart."
    )
    world.say(
        f"{guide.label} nodded. \"Arithmetic can tell you how many,\" {guide.pronoun('subject').capitalize()} said, "
        f"\"but philosophy can help you choose what to do with them.\""
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Nora",
         hero_type: str = "badger", guide_type: str = "tortoise") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="character", type=hero_type, label=hero_name,
        traits=["little", "thoughtful"], meters={"prize_count": 3}, memes={}
    ))
    guide = world.add(Entity(
        id="guide", kind="character", type=guide_type, label="Old Timo",
        traits=["wise", "slow"], memes={}
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=guide.id,
        plural=prize_cfg.plural, meters={"shared": 0}
    ))

    world.facts.update(hero=hero, guide=guide, prize=prize, activity=activity, setting=setting)

    world.say(f"{hero_name} was a little {hero_type} who loved arithmetic.")
    world.say(
        f"Every morning, {hero_name} counted {prize.phrase} in {setting.place}, "
        f"and the counting made {hero.pronoun('object')} feel important."
    )
    world.say(
        f"But {setting.place} had a {setting.mood} stillness, and {hero_name} began to wonder "
        f"why counting alone never answered the bigger questions."
    )

    world.para()
    world.say(
        f"One day, {guide.label} met {hero_name} near the path of {setting.place}."
    )
    question_thought(world, guide, hero, prize, activity)
    hesitate(world, hero, prize)
    world.say(
        f"{hero_name} wanted to {activity.rush}, yet the question kept tapping at {hero.pronoun('possessive')} mind."
    )

    world.para()
    world.say(
        f"So {hero_name} sat still, counted again, and then counted the space between the numbers."
    )
    share(world, hero, guide, prize)
    resolution(world, hero, guide, prize)

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "orchard": Setting(place="the orchard", mood="golden", affords={"count"}),
    "meadow": Setting(place="the meadow", mood="windy", affords={"count"}),
    "courtyard": Setting(place="the courtyard", mood="quiet", affords={"count"}),
}

ACTIVITIES = {
    "counting": Activity(
        id="counting",
        verb="count the apples",
        gerund="counting apples",
        rush="run to the next tree to count more",
        action_noun="counting",
        measure="numbers",
        weather="clear",
        tags={"arithmetic"},
    ),
    "sorting": Activity(
        id="sorting",
        verb="sort the stones",
        gerund="sorting stones",
        rush="gather every stone in a pile",
        action_noun="sorting",
        measure="groups",
        weather="clear",
        tags={"arithmetic"},
    ),
}

PRIZES = {
    "apples": Prize(label="apples", phrase="three apples", type="apples", region="basket", plural=True),
    "stones": Prize(label="stones", phrase="three smooth stones", type="stones", region="pouch", plural=True),
}

GUIDES = {
    "tortoise": Guide(
        id="tortoise",
        label="Old Timo",
        question="What changes when you share?",
        reply="The number gets smaller, but the friendship gets bigger.",
        transform="shares",
    ),
    "owl": Guide(
        id="owl",
        label="Mira Owl",
        question="What is a number for?",
        reply="A number can measure, but it cannot decide what is wise.",
        transform="reflects",
    ),
}

GIRL_NAMES = ["Nora", "Mina", "Lila", "Ivy", "Ada"]
BOY_NAMES = ["Bram", "Oren", "Pax", "Theo", "Ezra"]
TRAITS = ["curious", "quiet", "thoughtful", "bright", "restless"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    guide: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, prize, act = f["hero"], f["guide"], f["prize"], f["activity"]
    return [
        f'Write a short fable for a child about arithmetic, philosophy, and transformation that mentions {prize.phrase}.',
        f"Tell a gentle story where {hero.label} the {hero.type} counts {prize.phrase} and learns a wiser way from {guide.label}.",
        f"Write a small moral tale about a character who thinks about numbers, then changes because of a wise question.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, prize, act, setting = f["hero"], f["guide"], f["prize"], f["activity"], f["setting"]
    return [
        QAItem(
            question=f"What did {hero.label} love doing in {setting.place}?",
            answer=f"{hero.label} loved arithmetic and counted {prize.phrase} again and again.",
        ),
        QAItem(
            question=f"Who asked the question that changed {hero.label}'s thinking?",
            answer=f"{guide.label} asked a wise philosophy question that made {hero.label} stop and think.",
        ),
        QAItem(
            question=f"What transformation happened in the story?",
            answer=(
                f"{hero.label} changed from only counting to understanding that sharing could matter "
                f"more than keeping every {prize.label}."
            ),
        ),
        QAItem(
            question=f"What did {hero.label} do at the end with the {prize.label}?",
            answer=f"{hero.label} gave two {prize.label} to {guide.label} and kept one, so the scene turned generous.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is arithmetic?",
            answer="Arithmetic is the part of math that helps us count, add, subtract, and compare amounts.",
        ),
        QAItem(
            question="What is philosophy?",
            answer="Philosophy is thinking carefully about big questions like what is fair, true, or wise.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means a big change, like when someone's idea, feeling, or form becomes something new.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orchard", activity="counting", prize="apples", guide="tortoise",
                name="Nora", gender="girl", trait="curious"),
    StoryParams(place="meadow", activity="sorting", prize="stones", guide="owl",
                name="Bram", gender="boy", trait="thoughtful"),
]


def explain_rejection(place: str, activity: str, prize: str) -> str:
    return f"(No story: {place} does not fit {activity} with {prize} in this fable world.)"


ASP_RULES = r"""
% Facts:
% place(P). activity(A). prize(K). affords(P,A). guide(G).
% The world is valid when a place affords an activity and the prize can be
% counted and then shared after a wise question.
valid(P,A,K,G) :- affords(P,A), prize(K), activity(A), place(P), guide(G).
turns(P,A,K,G) :- valid(P,A,K,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for kid in PRIZES:
        lines.append(asp.fact("prize", kid))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set((p, a, k, g) for p, a, k in valid_combos() for g in GUIDES)
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos × guides).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(a - p))
    print("only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world: arithmetic, philosophy, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    guide = args.guide or rng.choice(list(GUIDES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, guide=guide,
                       name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 GUIDE := params.guide, hero_name=params.name)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos (place, activity, prize, guide):\n")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
