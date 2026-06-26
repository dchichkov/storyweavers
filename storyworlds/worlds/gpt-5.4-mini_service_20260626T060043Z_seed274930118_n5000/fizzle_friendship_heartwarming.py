#!/usr/bin/env python3
"""
storyworlds/worlds/fizzle_friendship_heartwarming.py
====================================================

A small story world about a warm friendship moment that begins with a plan
fizzling out and ends in kindness, repair, and shared joy.

The world is built from a simple seed tale:
- a child wants to do something sweet for a friend,
- the plan fizzes or fails in a harmless way,
- feelings wobble,
- a gentle helper move turns the moment into a heartwarming ending.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing"
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

    def __post_init__(self) -> None:
        for k in ("warmth", "tired", "ruined", "messy"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "love", "worry", "sad", "repair", "disappointment", "gratitude"):
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
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    verb: str
    gerund: str
    fizz: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


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


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amt: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_meme(ent: Entity, key: str, amt: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def tell(setting: Setting, plan: Plan, gift_cfg: Gift, fix_cfg: Fix,
         hero_name: str = "Mina", hero_type: str = "girl",
         friend_name: str = "Iris", friend_type: str = "girl",
         parent_type: str = "mother", trait: str = "gentle") -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["kind", "patient"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    gift = world.add(Entity(
        id="gift", type=gift_cfg.label, label=gift_cfg.label, phrase=gift_cfg.phrase,
        owner=hero.id, caretaker=parent.id, plural=gift_cfg.plural,
    ))
    fix = world.add(Entity(
        id=fix_cfg.id, type="fix", label=fix_cfg.label, owner=hero.id, caretaker=parent.id
    ))

    # Act 1: warm setup.
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved {friend.id} and liked making small surprises."
    )
    world.say(
        f"{friend.id} was {hero.id}'s best friend, and {hero.id} wanted to share something that would make {friend.id} smile."
    )
    world.say(
        f"That day, {hero.id}'s {parent.type if parent_type in {'mother','father'} else 'parent'} had helped with {gift.phrase}."
    )
    gift.worn_by = hero.id
    _add_meme(hero, "love", 1)
    _add_meme(friend, "love", 1)

    world.para()

    # Act 2: the plan fizzles.
    world.say(f"One day, {hero.id} and {friend.id} met at {setting.place}.")
    world.say(f"{hero.id} wanted to {plan.verb}, but something made the plan fizzle.")
    _add_meme(hero, "worry", 1)
    _add_meme(hero, "disappointment", 1)
    _add_meme(friend, "sad", 1)
    _add_meme(friend, "worry", 1)
    _add_meter(gift, "ruined", 1 if plan.id in {"paint_card", "balloon_note"} else 0)
    if plan.id == "bubble_speech":
        _add_meter(hero, "messy", 1)
        world.say(f"The bubbles were pretty for a moment, then they popped too fast and left only a tiny fizz of foam.")
    elif plan.id == "paint_card":
        _add_meter(gift, "ruined", 1)
        world.say(f"The paint smeared before it could dry, so the card looked messy instead of bright.")
    elif plan.id == "song_serenade":
        _add_meter(hero, "tired", 1)
        world.say(f"{hero.id} forgot the words halfway through, and the little song fizzled into a shy whisper.")
    else:
        world.say(f"The surprise wobbled and fizzled before it could become the sweet moment {hero.id} hoped for.")

    world.say(f"{hero.id} felt small and sad, and {friend.id} went quiet too.")

    world.para()

    # Act 3: repair and warmth.
    _add_meme(hero, "repair", 1)
    _add_meme(friend, "gratitude", 1)
    _add_meme(hero, "joy", 1)
    _add_meme(friend, "joy", 1)
    world.say(f"{hero.id}'s {parent.type if parent_type in {'mother','father'} else 'parent'} knelt beside them and smiled softly.")
    world.say(f'"We can fix a fizzle," {hero.pronoun("subject")} said. "Kindness still counts."')
    world.say(f"{hero.id} used {fix.label} and tried again in a simpler way.")
    world.say(f"{friend.id} helped, and that made the moment feel even warmer.")
    world.say(
        f"By the end, {hero.id} and {friend.id} were laughing together, and the little surprise had turned into a shared happy memory."
    )
    if gift_cfg.label == "card":
        world.say(f"The card was no longer fancy, but it was full of honest words and careful hearts.")
    elif gift_cfg.label == "note":
        world.say(f"The note was plain, yet it carried more love than anything shiny could have done.")
    else:
        world.say(f"The gift stayed simple, but the friendship around it felt bright and strong.")

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        gift=gift,
        fix=fix,
        plan=plan,
        setting=setting,
        resolved=True,
        fizzled=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"paint_card", "song_serenade"}),
    "porch": Setting(place="the porch", indoor=False, affords={"bubble_speech", "song_serenade"}),
    "garden": Setting(place="the garden", indoor=False, affords={"paint_card", "bubble_speech"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"paint_card", "song_serenade"}),
}

PLANS = {
    "bubble_speech": Plan(
        id="bubble_speech",
        verb="blow bubble letters for a message",
        gerund="blowing bubble letters",
        fizz="the bubbles popped too soon",
        effect="tiny foam on the air",
        keyword="fizzle",
        tags={"bubbles", "air"},
    ),
    "paint_card": Plan(
        id="paint_card",
        verb="paint a bright friendship card",
        gerund="painting a friendship card",
        fizz="the paint smeared before drying",
        effect="wet colors",
        keyword="fizzle",
        tags={"paint", "card"},
    ),
    "song_serenade": Plan(
        id="song_serenade",
        verb="sing a tiny friendship song",
        gerund="singing a tiny song",
        fizz="the words slipped away halfway through",
        effect="shy silence",
        keyword="fizzle",
        tags={"song", "voice"},
    ),
}

GIFTS = {
    "card": Gift("card", "card", "a hand-made friendship card", "torso"),
    "note": Gift("note", "note", "a folded note with kind words", "torso"),
    "bracelet": Gift("bracelet", "bracelet", "a little friendship bracelet", "wrist"),
}

FIXES = {
    "crayon": Fix("crayon", "a crayon", "use a crayon instead of wet paint", "kept trying with simpler lines", helps={"paint_card"}),
    "steady_breath": Fix("steady_breath", "a steady breath", "slow down and try the song again more gently", "sang the words one by one", helps={"song_serenade"}),
    "small_straw": Fix("small_straw", "a small straw", "blow slower and make fewer bubbles", "made the bubbles float longer", helps={"bubble_speech"}),
    "kind_words": Fix("kind_words", "kind words", "write the message in plain, honest words", "made the note feel warmer", helps={"paint_card", "song_serenade", "bubble_speech"}),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Sana", "Tia"],
    "boy": ["Eli", "Noah", "Owen", "Milo", "Finn"],
}
FRIEND_NAMES = ["Iris", "Toby", "June", "Arlo", "Pia", "Wren"]
TRAITS = ["gentle", "shy", "cheerful", "careful", "thoughtful"]

CURATED = [
    dict(place="kitchen", plan="paint_card", gift="card", fix="crayon", hero="Mina", hero_type="girl", friend="Iris", friend_type="girl", parent="mother", trait="gentle"),
    dict(place="porch", plan="song_serenade", gift="note", fix="steady_breath", hero="Eli", hero_type="boy", friend="Toby", friend_type="boy", parent="father", trait="shy"),
    dict(place="garden", plan="bubble_speech", gift="bracelet", fix="small_straw", hero="Nora", hero_type="girl", friend="Pia", friend_type="girl", parent="mother", trait="thoughtful"),
]


@dataclass
class StoryParams:
    place: str
    plan: str
    gift: str
    fix: str
    name: str
    gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming friendship story world with a fizzling plan.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    for place, s in SETTINGS.items():
        for plan_id in s.affords:
            for gift_id in GIFTS:
                for fix_id, fix in FIXES.items():
                    if plan_id in fix.helps:
                        out.append((place, plan_id, gift_id, fix_id))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.plan is None or c[1] == args.plan)
              and (args.gift is None or c[2] == args.gift)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, plan, gift, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice(FRIEND_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place, plan, gift, fix, name, gender, friend, friend_gender, parent, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    plan = f["plan"]
    gift = f["gift"]
    return [
        f'Write a heartwarming story for a young child that includes the word "fizzle" and ends with friendship feeling stronger.',
        f"Tell a gentle story about {hero.id} and {friend.id} when {hero.id} tries to {plan.verb} with {gift.phrase}, but the plan fizzles and they repair it kindly.",
        f"Write a small, child-friendly story where a friendship surprise does not go smoothly at first, then becomes sweet again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    plan = f["plan"]
    gift = f["gift"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do for {friend.id}?",
            answer=f"{hero.id} wanted to {plan.verb} with {gift.phrase} as a sweet friendship surprise.",
        ),
        QAItem(
            question=f"Why did the plan fizzle?",
            answer=f"It fizzled because {plan.fizz}, so the first try did not work the way {hero.id} hoped.",
        ),
        QAItem(
            question=f"How did they make things better after the fizzle?",
            answer=f"They used {fix.label} and tried again in a simpler, kinder way, which helped the friendship feel warm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind relationship where people care about each other, help each other, and like spending time together.",
        ),
        QAItem(
            question="What does it mean when something fizzles?",
            answer="When something fizzles, it starts or happens in a small weak way and then stops working or runs out too soon.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
fizzles(P) :- plan(P).
fizzles(P) :- plan_fails(P).

heartwarming(S) :- friendship(S), repair(S), joy(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s_id in SETTINGS:
        lines.append(asp.fact("setting", s_id))
        for p in SETTINGS[s_id].affords:
            lines.append(asp.fact("affords", s_id, p))
    for p_id in PLANS:
        lines.append(asp.fact("plan", p_id))
    for g_id in GIFTS:
        lines.append(asp.fact("gift", g_id))
    for f_id, f in FIXES.items():
        lines.append(asp.fact("fix", f_id))
        for h in sorted(f.helps):
            lines.append(asp.fact("helps", f_id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show plan/1."))
    asp_plans = sorted(set(asp.atoms(model, "plan")))
    py_plans = sorted((k,) for k in PLANS)
    if set(asp_plans) == set(py_plans):
        print(f"OK: clingo gate matches registry plans ({len(asp_plans)} plans).")
        return 0
    print("MISMATCH between clingo and Python plans.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show helps/2."))
    return sorted(set(asp.atoms(model, "helps")))


def generate(params: StoryParams) -> StorySample:
    hero_type = params.gender
    friend_type = params.friend_gender
    world = tell(
        SETTINGS[params.place],
        PLANS[params.plan],
        GIFTS[params.gift],
        FIXES[params.fix],
        hero_name=params.name,
        hero_type=hero_type,
        friend_name=params.friend,
        friend_type=friend_type,
        parent=params.parent,
        trait=params.trait,
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
        print(asp_program("#show helps/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show helps/2."))
        print(sorted(set(asp.atoms(model, "helps"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for item in CURATED:
            params = StoryParams(
                place=item["place"],
                plan=item["plan"],
                gift=item["gift"],
                fix=item["fix"],
                name=item["hero"],
                gender=item["hero_type"],
                friend=item["friend"],
                friend_gender=item["friend_type"],
                parent=item["parent"],
                trait=item["trait"],
            )
            samples.append(generate(params))
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
            header = f"### {p.name}: {p.plan} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
