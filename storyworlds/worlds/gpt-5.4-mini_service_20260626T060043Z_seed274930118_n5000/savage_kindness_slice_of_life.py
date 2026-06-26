#!/usr/bin/env python3
"""
storyworlds/worlds/savage_kindness_slice_of_life.py
===================================================

A small slice-of-life story world about a sharp little moment, a hurt feeling,
and a kindness that turns the day around.

The seed premise is simple:
- someone says something savage
- someone gets stung
- a kind repair changes the mood
- the ending proves the warmth is real

The world stays grounded in ordinary places and ordinary objects: lunch trays,
lost pencils, spilled juice, sidewalk chalk, and the tiny social physics of
being with other people.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Act:
    id: str
    verb: str
    gerund: str
    mess: str
    mood_shift: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    target: str
    plural: bool = False


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

    def chars(self) -> list[Entity]:
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _act_savage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.chars():
        if actor.memes.get("savage", 0.0) < THRESHOLD:
            continue
        for other in world.chars():
            if other.id == actor.id:
                continue
            sig = ("sting", actor.id, other.id)
            if sig in world.fired:
                continue
            if other.memes.get("stung", 0.0) >= THRESHOLD:
                continue
            world.fired.add(sig)
            other.memes["hurt"] = other.memes.get("hurt", 0.0) + 1
            other.memes["quiet"] = other.memes.get("quiet", 0.0) + 1
            out.append(f"{other.id} went quiet for a moment.")
            return out
    return out


def _act_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.chars():
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        for other in world.chars():
            if other.id == actor.id:
                continue
            sig = ("soften", actor.id, other.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            other.memes["trust"] = other.memes.get("trust", 0.0) + 1
            other.memes["hurt"] = max(0.0, other.memes.get("hurt", 0.0) - 1)
            out.append(f"{other.id} looked up again.")
            return out
    return []

CAUSAL_RULES = [_act_savage, _act_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def select_repair(act: Act) -> Optional[Repair]:
    for rep in REPAIRS:
        if act.id in rep.helps:
            return rep
    return None


def predict(world: World, actor: Entity, act: Act) -> dict:
    sim = world.copy()
    sim.get(actor.id).memes["savage"] = sim.get(actor.id).memes.get("savage", 0.0) + 1
    propagate(sim, narrate=False)
    hurt = sum(e.memes.get("hurt", 0.0) for e in sim.chars())
    trust = sum(e.memes.get("trust", 0.0) for e in sim.chars())
    return {"hurt": hurt, "trust": trust}


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quick-witted")
    world.say(f"{hero.id} was a little {trait} {hero.type} who noticed everything in the room.")


def setup_day(world: World, hero: Entity, friend: Entity, act: Act) -> None:
    if world.setting.indoor:
        world.say(f"It was a busy day inside {world.setting.place}, with chairs, cups, and pencils everywhere.")
    else:
        world.say(f"It was a calm day at {world.setting.place}, with sunlight on the ground and people coming and going.")
    world.say(f"{hero.id} loved talking with {friend.id} and always had a sharp little comment ready.")
    world.say(f"{hero.id} even liked to be a little savage when something felt funny.")


def say_savage(world: World, hero: Entity, friend: Entity, act: Act) -> None:
    hero.memes["savage"] = hero.memes.get("savage", 0.0) + 1
    world.say(
        f"When {friend.id} made a small mistake, {hero.id} gave a savage grin and said, "
        f"'{friend.id}, that was a pretty brave way to {act.verb}.'"
    )
    propagate(world, narrate=True)


def hurt_beats(world: World, friend: Entity, act: Act) -> None:
    if friend.memes.get("hurt", 0.0) >= THRESHOLD:
        world.say(
            f"{friend.id} blinked fast and stared at the floor. "
            f"The joke had landed too sharp."
        )


def repair_offer(world: World, hero: Entity, friend: Entity, act: Act) -> Optional[Repair]:
    rep = select_repair(act)
    if rep is None:
        return None
    world.say(
        f"Then {hero.id} looked back at {friend.id}, took a breath, and said, "
        f"'{rep.prep}'"
    )
    return rep


def accept_kindness(world: World, hero: Entity, friend: Entity, act: Act, rep: Repair) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(
        f"{hero.id} slid {rep.label} over and added, "
        f"'{rep.tail}'"
    )
    propagate(world, narrate=True)
    friend.memes["hurt"] = 0.0
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1
    hero.memes["savage"] = max(0.0, hero.memes.get("savage", 0.0) - 1)
    world.say(
        f"{friend.id} smiled a little. Soon the two of them were back to {act.gerund}, "
        f"but now the joke had softened into a shared laugh."
    )


def tell(setting: Setting, act: Act, repair: Repair, hero_name: str = "Mina",
         hero_type: str = "girl", friend_name: str = "Toby",
         friend_type: str = "boy", hero_trait: str = "quick-witted") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", hero_trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["little", "careful"]))
    prop = world.add(Entity(id="prop", type="thing", label="paper cup", phrase="a paper cup", owner=friend.id))

    introduce(world, hero)
    setup_day(world, hero, friend, act)
    world.para()
    world.say(f"{friend.id} was trying to {act.verb} when the cup tipped and rolled across the table.")
    say_savage(world, hero, friend, act)
    hurt_beats(world, friend, act)
    world.para()
    world.say(f"{hero.id} saw the way {friend.id} went quiet and realized the remark had been too savage.")
    rep = repair_offer(world, hero, friend, act)
    if rep is None:
        raise StoryError("No gentle repair exists for this activity.")
    accept_kindness(world, hero, friend, act, rep)

    world.facts.update(hero=hero, friend=friend, act=act, repair=rep, setting=setting, prop=prop)
    return world


SETTINGS = {
    "cafeteria": Setting(place="the cafeteria", indoor=True, affords={"spill", "share", "wait"}),
    "playground": Setting(place="the playground", indoor=False, affords={"spill", "share", "wait"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"spill", "share", "wait"}),
    "porch": Setting(place="the porch", indoor=False, affords={"spill", "share", "wait"}),
}

ACTS = {
    "spill": Act(
        id="spill",
        verb="carry lunch without wobbling",
        gerund="carrying lunch",
        mess="spill",
        mood_shift="embarrassed",
        keyword="spill",
        tags={"spill", "cup", "lunch"},
    ),
    "share": Act(
        id="share",
        verb="share a snack",
        gerund="sharing a snack",
        mess="crumbs",
        mood_shift="warm",
        keyword="share",
        tags={"share", "snack"},
    ),
    "wait": Act(
        id="wait",
        verb="wait for the others",
        gerund="waiting quietly",
        mess="nothing",
        mood_shift="patient",
        keyword="wait",
        tags={"wait", "queue"},
    ),
}

REPAIRS = [
    Repair(
        id="napkin",
        label="a napkin",
        prep="I was rude. Let me help clean that up.",
        tail="I'll clean this with you",
        helps={"spill"},
        target="mess",
    ),
    Repair(
        id="cookie",
        label="an extra cookie",
        prep="I shouldn't have said that. Want to split this cookie?",
        tail="we can share this instead",
        helps={"share"},
        target="warmth",
    ),
    Repair(
        id="sticker",
        label="a bright sticker",
        prep="That came out too sharp. Here, I saved you a sticker.",
        tail="you can have the first pick",
        helps={"wait"},
        target="patience",
    ),
]

NAMES = ["Mina", "Noah", "Lila", "Toby", "Zara", "Eli", "Iris", "Owen"]
TRAITS = ["quick-witted", "sly", "funny", "bright", "sharp", "playful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for act in s.affords:
            if select_repair(ACTS[act]):
                combos.append((place, act))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a savage moment and a kindness repair.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, friend=friend, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a child that includes the word "savage" and ends with kindness.',
        f"Tell a small story where {f['hero'].id} makes a savage joke, then repairs it with a kind gesture.",
        f"Write a gentle everyday story set at {f['setting'].place} about a sharp remark that becomes a warm moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, act, rep = f["hero"], f["friend"], f["act"], f["repair"]
    return [
        QAItem(
            question=f"Who said the savage thing in the story?",
            answer=f"{hero.id} said the savage remark, but then {hero.id} noticed it had stung {friend.id}.",
        ),
        QAItem(
            question=f"What was {friend.id} trying to do when the joke landed too hard?",
            answer=f"{friend.id} was trying to {act.verb}, and the small mistake made the moment awkward.",
        ),
        QAItem(
            question=f"How did the story turn from mean to kind?",
            answer=f"{hero.id} offered {rep.label} and said sorry in a plain, honest way, which helped the room feel softer.",
        ),
        QAItem(
            question=f"What did the two kids do at the end?",
            answer=f"They went back to {act.gerund}, and this time they were smiling together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does savage mean in a playground or lunchroom kind of story?",
            answer="Here, savage means a sharp or extra-bold comment that can sound funny to one person but sting another person.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is doing or saying something gentle that helps another person feel safer, calmer, or cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTS.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for rid, r in enumerate(REPAIRS):
        lines.append(asp.fact("repair", r.id))
        for a in sorted(r.helps):
            lines.append(asp.fact("helps", r.id, a))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act) :- affords(Place, Act), repair(Rep), helps(Rep, Act).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTS[params.activity], REPAIRS[0], params.name, "girl" if params.name in {"Mina", "Lila", "Zara", "Iris"} else "boy", params.friend, "boy", params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="cafeteria", activity="spill", name="Mina", friend="Toby", trait="sharp"),
    StoryParams(place="playground", activity="wait", name="Zara", friend="Eli", trait="funny"),
    StoryParams(place="kitchen", activity="share", name="Lila", friend="Noah", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity) combos:")
        for place, act in combos:
            print(f"  {place:10} {act}")
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
