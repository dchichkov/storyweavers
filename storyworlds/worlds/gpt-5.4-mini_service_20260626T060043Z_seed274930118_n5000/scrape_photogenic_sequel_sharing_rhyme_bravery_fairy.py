#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/scrape_photogenic_sequel_sharing_rhyme_bravery_fairy.py
=============================================================================================================

A small fairy-tale story world about a child, a fragile treasure, and a brave
shared solution.

Seed premise:
---
A young fairy-tale helper wants to make a photogenic sequel to an old picture
storybook. The best path to the moonlit grove is pretty, but it has thorny
arches and rough stone steps that can scrape bright clothes and a favorite prop.
A worried companion warns about the damage. The hero hesitates, then uses
sharing, rhyme, and bravery to choose a safer way and still reach the ending
image.

World model:
---
- Physical meters track scrape damage, dust, and shine.
- Emotional memes track longing, worry, bravery, joy, and shared goodwill.
- The story is driven by simulated state, not by swapping names into one fixed
  paragraph.
- The key conflict is whether the hero can keep a photogenic prize safe while
  still making the sequel.

Narrative instruments:
---
- Sharing: a lantern, a map, a dress-up prop, or a turn-taking plan can be
  shared to make the path easier.
- Rhyme: a small rhyme helps calm fear and guide the next choice.
- Bravery: the hero crosses the risky place anyway, but with a wiser plan.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["scrape", "dust", "shine", "care"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "bravery", "joy", "sharing"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "princess", "queen", "mother", "mom", "woman"}
        male = {"boy", "prince", "king", "father", "dad", "man"}
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
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Path:
    id: str
    verb: str
    gerund: str
    risk: str
    mess: str
    zone: set[str]
    hint: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    offer: str
    ending: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _apply_scrape(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["scrape"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("scrape", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scrape"] += 1
            item.meters["dust"] += 1
            out.append(f"{actor.id}'s {item.label} picked up a scrape and a little dust.")
    return out


def _apply_shine(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["scrape"] < THRESHOLD:
            continue
        if item.caretaker and ("shine", item.id) not in world.fired:
            world.fired.add(("shine", item.id))
            carer = world.get(item.caretaker)
            carer.memes["worry"] += 1
            out.append(f"That would take time to polish, and {carer.id} worried about the finish.")
    return out


def _apply_bravery(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["bravery"] < THRESHOLD:
            continue
        sig = ("bravery", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"{actor.id} stood straighter, because brave hearts can still choose carefully.")
    return out


CAUSAL_RULES = [_apply_scrape, _apply_shine, _apply_bravery]


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


def path_at_risk(path: Path, prize: Prize) -> bool:
    return prize.region in path.zone


def select_gear(path: Path, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if path.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_scrape(world: World, actor: Entity, path: Path, prize_id: str) -> dict:
    sim = world.copy()
    _do_path(sim, sim.get(actor.id), path, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"scraped": bool(prize and prize.meters["scrape"] >= THRESHOLD)}


def _do_path(world: World, actor: Entity, path: Path, narrate: bool = True) -> None:
    if path.id not in world.setting.affords:
        return
    world.zone = set(path.zone)
    actor.meters[path.mess] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    kind = next((t for t in hero.traits if t != "little"), hero.type)
    world.say(
        f"{hero.id} was a little {kind} {hero.type} who loved bright endings and tidy magic."
    )


def loves_sequel(world: World, hero: Entity, path: Path) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} wanted to make a photogenic sequel, so {hero.pronoun()} practiced "
        f"{path.gerund} and imagined the moonlight catching every pretty edge."
    )


def has_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["sharing"] += 1
    prize.worn_by = hero.id
    world.say(
        f"A dear grown-up gave {hero.id} {hero.pronoun('object')} {prize.phrase}, and "
        f"{hero.id} loved {prize.it()} like a treasure from the first story."
    )


def arrive(world: World, hero: Entity, friend: Entity, path: Path) -> None:
    world.say(
        f"One evening, {hero.id} and {friend.id} went to {world.setting.place}, "
        f"where {path.hint}"
    )


def warn(world: World, friend: Entity, hero: Entity, path: Path, prize: Entity) -> bool:
    pred = predict_scrape(world, hero, path, prize.id)
    if not pred["scraped"]:
        return False
    friend.memes["worry"] += 1
    world.facts["predicted_scrape"] = True
    world.say(
        f'"Be careful," {friend.id} said. "That path can scrape {hero.pronoun("possessive")} '
        f"{prize.label} and spoil the photogenic sequel.""
    )
    return True


def hesitate(world: World, hero: Entity, path: Path) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} looked at the rough stones and hesitated, because the old path was pretty "
        f"but sharp."
    )
    world.say(f"{hero.id} tried to {path.verb},")


def share_plan(world: World, friend: Entity, hero: Entity, path: Path, prize: Entity) -> None:
    hero.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    gear = select_gear(path, prize)
    if gear is None:
        return
    world.say(
        f"Then {friend.id} smiled and offered a shared plan: {gear.offer}."
    )
    return gear


def rhyme(world: World, hero: Entity, path: Path) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} whispered a rhyme: \"Step by step, and light by light, / "
        f"we keep the sequel warm and bright.\""
    )


def brave_cross(world: World, hero: Entity, friend: Entity, path: Path, prize: Entity, gear: Gear) -> None:
    hero.memes["bravery"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} took a brave breath, put on {gear.label}, and crossed together with {friend.id}."
    )
    world.say(
        f"They {gear.ending}. At the end, {hero.id} could still hold {hero.pronoun('possessive')} "
        f"{prize.label}, and it stayed bright enough for the sequel picture."
    )


def tell(setting: Setting, path: Path, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "fairy",
         hero_traits: Optional[list[str]] = None, friend_type: str = "mouse") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["kind", "curious"])))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_type, label="the friend"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=friend.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_sequel(world, hero, path)
    has_prize(world, hero, prize)
    world.para()
    arrive(world, hero, friend, path)
    warn(world, friend, hero, path, prize)
    hesitate(world, hero, path)
    gear = share_plan(world, friend, hero, path, prize)
    world.say(f"Sharing made the path feel less lonely.")
    rhyme(world, hero, path)
    world.para()
    if gear:
        brave_cross(world, hero, friend, path, prize, gear)
    world.facts.update(hero=hero, friend=friend, prize=prize, prize_cfg=prize_cfg, path=path, gear=gear)
    return world


SETTINGS = {
    "moon_grove": Setting(place="the moonlit grove", outdoor=True, affords={"stone_bridge", "rose_arch"}),
    "castle_gate": Setting(place="the castle gate", outdoor=True, affords={"stone_bridge"}),
    "storybook_lane": Setting(place="the storybook lane", outdoor=True, affords={"rose_arch", "stone_bridge"}),
}


PATHS = {
    "stone_bridge": Path(
        id="stone_bridge",
        verb="cross the stone bridge",
        gerund="crossing the stone bridge",
        risk="scrape",
        mess="scrape",
        zone={"feet", "legs"},
        hint="the steps were narrow and rough, like a page with a jagged edge.",
        keyword="bridge",
        tags={"scrape", "stone", "fairy"},
    ),
    "rose_arch": Path(
        id="rose_arch",
        verb="walk through the rose arch",
        gerund="walking through the rose arch",
        risk="scrape",
        mess="scrape",
        zone={"torso", "arms"},
        hint="the arch was lovely, but its thorns could scrape sleeves and ribbons.",
        keyword="rose",
        tags={"scrape", "rose", "fairy"},
    ),
}


PRIZES = {
    "cape": Prize(id="cape", label="cape", phrase="a shimmer-bright cape", region="torso"),
    "ribbon": Prize(id="ribbon", label="ribbon", phrase="a silver ribbon", region="torso"),
    "shoes": Prize(id="shoes", label="shoes", phrase="glass shoes", region="feet", plural=True),
}


GEAR = [
    Gear(id="boots", label="soft boots", covers={"feet"}, guards={"scrape"}, offer="share the soft boots and take the kinder steps", ending="walked on the smoothest stones"),
    Gear(id="shawl", label="a shared shawl", covers={"torso", "arms"}, guards={"scrape"}, offer="share a shawl so the thorns cannot catch the cloth", ending="slipped by the thorns without a tear"),
    Gear(id="gloves", label="tiny gloves", covers={"hands"}, guards={"scrape"}, offer="share tiny gloves for the climbing and the holding", ending="kept their hands safe while they climbed"),
]


GIRL_NAMES = ["Mina", "Tilly", "Rose", "Elia", "Nina", "Luna", "Faye", "Iris"]
BOY_NAMES = ["Theo", "Pip", "Bram", "Jules", "Oren", "Nico"]
TRAITS = ["kind", "curious", "gentle", "brave", "bright", "dreamy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid in setting.affords:
            path = PATHS[pid]
            for prize_id, prize in PRIZES.items():
                if path_at_risk(path, prize) and select_gear(path, prize):
                    combos.append((place, pid, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    path: str
    prize: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "scrape": [("What is a scrape?", "A scrape is a small scratch or mark made when something rubs against a rough surface.")],
    "sharing": [("What is sharing?", "Sharing means letting someone else use a thing or enjoy it with you.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a word pattern where sounds at the ends of words match or feel similar.")],
    "bravery": [("What is bravery?", "Bravery is trying something scary or hard while still doing your best.")],
    "photogenic": [("What does photogenic mean?", "Photogenic means something looks especially nice in a picture.")],
    "sequel": [("What is a sequel?", "A sequel is a new story, picture, or adventure that comes after an earlier one.")],
    "fairy": [("What is a fairy tale?", "A fairy tale is a story with magic, wonder, and brave choices, often with a happy ending.")],
}
KNOWLEDGE_ORDER = ["fairy", "photogenic", "sequel", "scrape", "sharing", "rhyme", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, path, prize = f["hero"], f["friend"], f["path"], f["prize_cfg"]
    return [
        f'Write a fairy tale about "{hero.id}" making a photogenic sequel while keeping a {prize.label} safe.',
        f"Tell a short story where {hero.id} and {friend.id} need {path.keyword} sharing, rhyme, and bravery to cross the path.",
        f'Write a child-friendly fairy story that includes the words "scrape", "photogenic", and "sequel".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, path = f["hero"], f["friend"], f["prize"], f["path"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to make at {world.setting.place}?",
            answer=f"{hero.id} was trying to make a photogenic sequel, which means a new picture-story that looked bright and lovely after the first tale.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the {path.keyword} path?",
            answer=f"{friend.id} worried because the rough path could scrape {hero.pronoun('possessive')} {prize.label} and spoil the pretty picture.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} solve the problem?",
            answer=f"They solved it by sharing {select_gear(path, prize).label if select_gear(path, prize) else 'help'}, whispering a rhyme, and using bravery to cross safely.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the brave plan worked?",
            answer=f"{hero.id} felt brave and happy, because {trait} {hero.id} could reach the end without ruining {hero.pronoun('possessive')} treasure.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["path"].tags) | {"fairy", "photogenic", "sequel"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_grove", path="rose_arch", prize="cape", name="Mina", gender="girl", friend="mouse", trait="gentle"),
    StoryParams(place="storybook_lane", path="stone_bridge", prize="shoes", name="Theo", gender="boy", friend="fox", trait="brave"),
    StoryParams(place="castle_gate", path="stone_bridge", prize="ribbon", name="Luna", gender="girl", friend="owl", trait="bright"),
]


def explain_rejection(path: Path, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not path_at_risk(path, prize):
        return (
            f"(No story: {path.gerund} does not reach the part of the body where {noun} sits, "
            f"so there is no honest scrape-risk and no reason for a warning.)"
        )
    return (
        f"(No story: the available gear does not both cover {prize.region} and guard against scrape for {noun}. "
        f"The compromise must truly protect the prize.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(P, R) :- worn_on(P, R), path_zone(A, R).
fix(P, A) :- prize_at_risk(P, R), gear(G), covers(G, R), guards(G, scrape), path_mess(A, scrape).
valid(Place, Path, Prize) :- affords(Place, Path), prize(Prize), path(Path), prize_at_risk(Prize, _), fix(Prize, Path).
valid_story(Place, Path, Prize, Gender) :- valid(Place, Path, Prize), wears(Gender, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", pid, p))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("path_mess", pid, p.mess))
        for z in sorted(p.zone):
            lines.append(asp.fact("path_zone", pid, z))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: scrape, photogenic sequel, sharing, rhyme, bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    if args.path and args.prize:
        path, prize = PATHS[args.path], PRIZES[args.prize]
        if not (path_at_risk(path, prize) and select_gear(path, prize)):
            raise StoryError(explain_rejection(path, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.path is None or c[1] == args.path)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, path_id, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(["mouse", "owl", "fox", "sparrow"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, path=path_id, prize=prize_id, name=name, gender=gender, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PATHS[params.path], PRIZES[params.prize], params.name, params.gender, [params.trait], params.friend)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, path, prize) combos ({len(stories)} with gender):\n")
        for place, path, prize in triples:
            genders = sorted(g for (pl, pa, pr, g) in stories if (pl, pa, pr) == (place, path, prize))
            print(f"  {place:14} {path:12} {prize:8}  [{', '.join(genders)}]")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.path} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
