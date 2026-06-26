#!/usr/bin/env python3
"""
A standalone storyworld for an Adventure-style quest with suspense and kindness.

Seed premise:
- A child sets out on a small quest.
- The path includes suspense, but the turning point comes from kindness.
- The story should feel like an adventure, with a clear beginning, middle turn,
  and ending image proving what changed.
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    search: str
    clue: str
    risk: str
    tension: str
    keyword: str = "emphasis"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    safe_for: set[str] = field(default_factory=set)


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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("suspense", 0.0) < THRESHOLD:
            continue
        sig = ("suspense", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1.0
        out.append(f"The path felt quiet, and {actor.id} listened very carefully.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for aid in world.entities.values():
        if aid.kind != "aid":
            continue
        if aid.meters.get("used", 0.0) < THRESHOLD:
            continue
        sig = ("kindness", aid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"That kind help made the hard part feel smaller.")
    return out


CAUSAL_RULES = [
    _r_suspense,
    _r_kindness,
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


def predict_risk(world: World, hero: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    prize = sim.get(prize_id)
    return {
        "lost": prize.location != "home" and prize.carried_by is None,
        "suspense": sim.get(hero.id).memes.get("suspense", 0.0),
    }


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} does not support this quest.)")
    hero.meters["travel"] = hero.meters.get("travel", 0.0) + 1.0
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1.0
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved a good adventure.")


def set_out(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    world.say(
        f"One day, {hero.id} began a quest to {quest.verb} and find {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept an emphasis on each clue, because {quest.clue} could matter."
    )


def warn(world: World, hero: Entity, quest: Quest, prize: Entity) -> bool:
    pred = predict_risk(world, hero, quest, prize.id)
    if not pred["lost"]:
        return False
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1.0
    world.say(
        f'"If we rush, your {prize.label} could get lost," {hero.pronoun("possessive")} helper said.'
    )
    return True


def hesitate(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1.0
    world.say(f"{hero.id} slowed down, because the path felt extra suspenseful.")
    world.say(f"{hero.pronoun().capitalize()} tried to {quest.search}, listening for every tiny sound.")


def offer_kindness(world: World, helper: Entity, hero: Entity, aid: Aid) -> Aid:
    world.say(
        f"Then {helper.id} offered {aid.label} and said, \"We can do this together.\""
    )
    return aid


def accept_kindness(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity, aid: Aid) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    hero.memes["suspense"] = 0.0
    prize.carried_by = hero.id
    prize.location = "home"
    aid_entity = world.get(aid.id)
    aid_entity.meters["used"] = aid_entity.meters.get("used", 0.0) + 1.0
    world.say(
        f"{hero.id} smiled and took {aid.label}. With {helper.pronoun('object')} beside {hero.pronoun('object')}, the search became brave instead of scary."
    )
    world.say(
        f"At last, {hero.id} found {hero.pronoun('possessive')} {prize.label}, and they went home in a happy line."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl",
         helper_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        location="path",
        plural=prize_cfg.plural,
    ))
    aid_def = AID(id="lantern", label="a small lantern", prep="hold up the lantern", tail="carried the lantern home", helps={"suspense"}, safe_for={"path"})
    aid = world.add(Entity(id=aid_def.id, kind="aid", type="aid", label=aid_def.label, protective=True))

    introduce(world, hero)
    world.para()
    set_out(world, hero, quest, prize)
    warn(world, hero, quest, prize)
    hesitate(world, hero, quest)
    world.para()
    offer_kindness(world, helper, hero, aid_def)
    accept_kindness(world, hero, helper, quest, prize, aid_def)

    world.facts.update(hero=hero, helper=helper, prize=prize, quest=quest, aid=aid_def, setting=setting)
    return world


SETTINGS = {
    "woods": Setting(place="the woods", kind="forest", affords={"search"}),
    "trail": Setting(place="the mountain trail", kind="trail", affords={"search"}),
    "harbor": Setting(place="the harbor path", kind="coast", affords={"search"}),
}

QUESTS = {
    "search": Quest(
        id="search",
        verb="search the path",
        gerund="searching the path",
        search="follow the tiny footprints",
        clue="the footprints pointed ahead",
        risk="the trail could feel lost in the dark",
        tension="the shadows made every step careful",
        tags={"quest", "suspense", "kindness", "adventure", "emphasis"},
    )
}

PRIZES = {
    "map": Prize(label="map", phrase="a folded paper map", type="map", location="path"),
    "ring": Prize(label="ring", phrase="a little brass ring", type="ring", location="path"),
    "shell": Prize(label="shell", phrase="a shiny shell charm", type="shell", location="path"),
}

GIRL_NAMES = ["Mina", "Lena", "Aria", "Nora", "Tess"]
BOY_NAMES = ["Owen", "Jasper", "Theo", "Eli", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, qid, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child named {f["hero"].id} that includes the word "emphasis".',
        f"Tell a suspenseful but kind quest story about {f['hero'].id} looking for a {f['prize'].label}.",
        f"Write a gentle adventure where a helper says they can do the search together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, quest = f["hero"], f["helper"], f["prize"], f["quest"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do?",
            answer=f"{hero.id} was trying to {quest.verb} and find {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because the path was quiet and {hero.id} had to search carefully for the {prize.label}.",
        ),
        QAItem(
            question=f"How did kindness help in the story?",
            answer=f"{helper.id} offered help and stayed beside {hero.id}, so the search felt safer and less scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to look for something important or to finish a special task.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling that makes you wonder what will happen next.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping someone, being gentle, and making them feel safe.",
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
    lines.append("== (3) World questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="woods", quest="search", prize="map", name="Mina", gender="girl", helper="mother"),
    StoryParams(place="trail", quest="search", prize="ring", name="Owen", gender="boy", helper="father"),
    StoryParams(place="harbor", quest="search", prize="shell", name="Lena", gender="girl", helper="mother"),
]


def explain_rejection() -> str:
    return "(No story: that choice does not fit this quest adventure.)"


ASP_RULES = r"""
place(woods). place(trail). place(harbor).
quest(search).
prize(map). prize(ring). prize(shell).

affords(woods,search).
affords(trail,search).
affords(harbor,search).

valid(Place,Quest,Prize) :- affords(Place,Quest), prize(Prize).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for pr in PRIZES:
        lines.append(asp.fact("prize", pr))
    for place, setting in SETTINGS.items():
        for q in setting.affords:
            lines.append(asp.fact("affords", place, q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure quest storyworld with suspense and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_rejection())
    place, quest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], PRIZES[params.prize],
                 params.name, params.gender, params.helper)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, quest, prize in combos:
            print(f"  {place:8} {quest:8} {prize:8}")
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
