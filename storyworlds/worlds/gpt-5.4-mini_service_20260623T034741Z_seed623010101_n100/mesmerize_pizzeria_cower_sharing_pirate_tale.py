#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/mesmerize_pizzeria_cower_sharing_pirate_tale.py
========================================================================================================================

A standalone story world for a tiny pirate-tale domain set in and around a
pizzeria. The child-facing story follows a small crew who are mesmerized by the
smell of pizza, then cower when the kitchen gets too hot or noisy, and finally
solve the problem through sharing.

Core premise:
- Pirates arrive at a pizzeria after a long, salty day at sea.
- The smell and shine of the pizza counter can mesmerize them.
- A loud moment or hot oven can make one crew member cower.
- A shared slice, shared job, or shared courage turns the mood around.

This script follows the Storyweavers contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and runs a smoke test story generation
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
    role: str = ""
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Craving:
    id: str
    verb: str
    noun: str
    smell: str
    shimmer: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareMove:
    id: str
    label: str
    action: str
    ending: str
    tags: set[str] = field(default_factory=set)


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

    def crew(self) -> list[Entity]:
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    setting: str = "harbor_pizzeria"
    craving: str = "pepper_pies"
    hero: str = "Milo"
    hero_type: str = "boy"
    mate: str = "Nina"
    mate_type: str = "girl"
    leader: str = "captain"
    share_move: str = "split_slice"
    seed: Optional[int] = None


SETTINGS = {
    "harbor_pizzeria": Setting(place="the harbor pizzeria", indoors=True, affordances={"bake", "serve", "share"}),
    "dockside_pizzeria": Setting(place="the dockside pizzeria", indoors=True, affordances={"bake", "serve", "share"}),
}

CRAVINGS = {
    "pepper_pies": Craving(
        id="pepper_pies",
        verb="stare at the pepper pies",
        noun="pepper pie",
        smell="the smell of warm cheese and herbs",
        shimmer="the shiny crust",
        risk="the hot oven",
        tags={"pizza", "pizzeria", "smell"},
    ),
    "golden_slices": Craving(
        id="golden_slices",
        verb="watch the golden slices",
        noun="golden slice",
        smell="the smell of tomato and bread",
        shimmer="the melted cheese",
        risk="the busy counter",
        tags={"pizza", "pizzeria", "smell"},
    ),
}

SHARES = {
    "split_slice": ShareMove(
        id="split_slice",
        label="split the slice",
        action="share one slice and pass the napkin",
        ending="they ate together with happy crumbs on their chins",
        tags={"sharing"},
    ),
    "share_jobs": ShareMove(
        id="share_jobs",
        label="share the jobs",
        action="share the work of carrying plates and calling orders",
        ending="the crew worked like a tidy team",
        tags={"sharing"},
    ),
}

GIRL_NAMES = ["Nina", "Tess", "Mara", "Luna", "Ivy"]
BOY_NAMES = ["Milo", "Jett", "Finn", "Otto", "Kai"]
LEADER_TYPES = ["captain", "mate"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CRAVINGS:
            for m in SHARES:
                out.append((s, c, m))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale in a pizzeria, with mesmerizing pizza and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--craving", choices=CRAVINGS)
    ap.add_argument("--share-move", choices=SHARES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-type", choices=["boy", "girl"])
    ap.add_argument("--leader", choices=LEADER_TYPES)
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
              and (args.craving is None or c[1] == args.craving)
              and (args.share_move is None or c[2] == args.share_move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, craving, share_move = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    mate_type = args.mate_type or ("girl" if hero_type == "boy" else "boy")
    hero = args.hero or rng.choice(BOY_NAMES if hero_type == "boy" else GIRL_NAMES)
    mate = args.mate or rng.choice(GIRL_NAMES if mate_type == "girl" else BOY_NAMES)
    if mate == hero:
        mate = next(n for n in (GIRL_NAMES + BOY_NAMES) if n != hero)
    leader = args.leader or rng.choice(LEADER_TYPES)
    return StoryParams(setting=setting, craving=craving, hero=hero, hero_type=hero_type,
                       mate=mate, mate_type=mate_type, leader=leader, share_move=share_move)


def _init_entity(ent: Entity) -> Entity:
    ent.meters.setdefault("hunger", 0.0)
    ent.meters.setdefault("heat", 0.0)
    ent.meters.setdefault("cower", 0.0)
    ent.meters.setdefault("mess", 0.0)
    ent.memes.setdefault("joy", 0.0)
    ent.memes.setdefault("wonder", 0.0)
    ent.memes.setdefault("fear", 0.0)
    ent.memes.setdefault("sharing", 0.0)
    return ent


def _shared_smoke(world: World) -> None:
    for kid in world.crew():
        if kid.meters["heat"] >= THRESHOLD and kid.memes["fear"] < THRESHOLD:
            kid.memes["fear"] += 1
        if kid.meters["cower"] >= THRESHOLD and kid.memes["fear"] >= THRESHOLD:
            kid.memes["joy"] += 0.5


def tell(setting: Setting, craving: Craving, share: ShareMove,
         hero: str, hero_type: str, mate: str, mate_type: str,
         leader: str) -> World:
    world = World(setting)
    hero_e = _init_entity(world.add(Entity(id=hero, kind="character", type=hero_type, role="hero")))
    mate_e = _init_entity(world.add(Entity(id=mate, kind="character", type=mate_type, role="mate")))
    crew = world.add(Entity(id="crew", kind="character", type="pirate", role="crew", plural=True))
    _init_entity(crew)
    oven = _init_entity(world.add(Entity(id="oven", kind="thing", type="oven", label="the oven")))
    pies = _init_entity(world.add(Entity(id="pies", kind="thing", type="thing", label="the pepper pies")))
    counter = _init_entity(world.add(Entity(id="counter", kind="thing", type="thing", label="the counter")))

    world.facts["setting"] = setting
    world.facts["craving"] = craving
    world.facts["share"] = share
    world.facts["leader"] = leader
    world.facts["hero"] = hero_e
    world.facts["mate"] = mate_e
    world.facts["crew"] = crew
    world.facts["oven"] = oven
    world.facts["pies"] = pies
    world.facts["counter"] = counter

    hero_e.memes["wonder"] += 1
    mate_e.memes["wonder"] += 1
    hero_e.meters["hunger"] += 1
    mate_e.meters["hunger"] += 1

    world.say(
        f"At {setting.place}, {hero_e.id} and {mate_e.id} came in like little pirates after a long sail. "
        f"{craving.smell} could {share.action} in a heartbeat."
    )
    world.say(
        f"{hero_e.id} and {mate_e.id} were mesmerized by {craving.smell} and {craving.shimmer}. "
        f"They leaned close to the glass like it held a treasure map."
    )

    world.para()
    hero_e.meters["heat"] += 1
    mate_e.meters["heat"] += 1
    crew.memes["joy"] += 1
    world.say(
        f"Then the kitchen door swung open and a rush of heat rolled out from {craving.risk}. "
        f"{mate_e.id} began to cower, and even brave {hero_e.id} took a step back."
    )
    _shared_smoke(world)

    world.para()
    mate_e.meters["cower"] += 1
    hero_e.memes["fear"] += 0.5
    if leader == "captain":
        world.say(
            f"The captain saw the wobble in the crew and said, \"We can share, not snatch. "
            f"Let us split the food and calm the deck.\""
        )
    else:
        world.say(
            f"The mate held up a hand and said, \"Easy now, crew. Sharing will keep every belly full.\""
        )
    world.say(
        f"So {hero_e.id} and {mate_e.id} shared the work at the counter, and the smell no longer felt like a trick."
    )

    world.para()
    hero_e.memes["sharing"] += 1
    mate_e.memes["sharing"] += 1
    hero_e.memes["joy"] += 1
    mate_e.memes["joy"] += 1
    hero_e.meters["hunger"] = 0
    mate_e.meters["hunger"] = 0
    hero_e.meters["heat"] = 0
    mate_e.meters["heat"] = 0
    world.say(
        f"At last they got one slice, and {share.action}. {share.ending}. "
        f"Their faces lit up, and the pizzeria smelled like a friendly ship at dinner."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    craving = f["craving"]
    share = f["share"]
    return [
        f'Write a pirate tale for a young child that includes the words "mesmerize", "pizzeria", and "cower".',
        f"Tell a short story about {f['hero'].id} and {f['mate'].id} in a pizzeria, where the smell of pizza can mesmerize them and sharing helps them feel safe.",
        f"Write a child-friendly pirate story where the crew learns to {share.action} instead of fighting over {craving.noun}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    craving: Craving = f["craving"]
    share: ShareMove = f["share"]
    setting: Setting = f["setting"]
    leader = f["leader"]
    qa = [
        QAItem(
            question=f"Who went to {setting.place} in this pirate tale?",
            answer=f"{hero.id} and {mate.id} went to {setting.place} like two little pirates. They came in together, and the story follows how they handled the pizza smell and the hot kitchen.",
        ),
        QAItem(
            question=f"Why were {hero.id} and {mate.id} mesmerized at the pizzeria?",
            answer=f"They were mesmerized by {craving.smell} and {craving.shimmer}. The pizza looked and smelled so good that it pulled their attention right to the glass counter.",
        ),
        QAItem(
            question=f"Why did {mate.id} cower when the kitchen door opened?",
            answer=f"{mate.id} cowered because a rush of heat came from {craving.risk}. The warm blast made the moment feel too big for a small pirate crew, so they stepped back.",
        ),
        QAItem(
            question=f"How did the crew solve the problem with sharing?",
            answer=f"They chose to {share.action}. That shared choice calmed the crew, and it let them enjoy the pizza without grabbing or squabbling.",
        ),
        QAItem(
            question=f"What did the captain say when the crew got worried?",
            answer=f"The {leader} told them to share instead of snatching. The advice gave them a safer way to stay together and keep the evening friendly.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did the ending show that sharing changed the story?",
            answer="They split the slice, the fear went down, and the crew ate together. The final picture is of happy pirates with full bellies and calmer hearts.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a pizzeria?",
            answer="A pizzeria is a place where people make and serve pizza. It often smells warm and tasty because there are ovens, cheese, and bread inside.",
        ),
        QAItem(
            question="What does mesmerize mean?",
            answer="To mesmerize someone means to hold their attention so strongly that they stare and forget other things. A bright or tasty sight can mesmerize a child for a little while.",
        ),
        QAItem(
            question="What does cower mean?",
            answer="To cower means to bend down or pull back because you feel scared. A child may cower when something feels loud, hot, or too sudden.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing helps because more than one person can enjoy the same good thing. It also lowers fighting, so a group can stay calm and happy together.",
        ),
    ]
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
need_share(S) :- story(S), mesmerized(S), cower(S).
mesmerized(S) :- sees_pizza(S), smell_good(S).
cower(S) :- hot_blast(S).
shared_end(S) :- need_share(S), share_move(S).
valid_story(Settings, Craving, Move) :- setting(Settings), craving(Craving), share_move(Move).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CRAVINGS:
        lines.append(asp.fact("craving", cid))
    for mid in SHARES:
        lines.append(asp.fact("share_move", mid))
    lines.append(asp.fact("story", "pirate_pizzeria"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import traceback
    ok = True
    try:
        py = set(valid_combos())
        asp_set = set(asp_valid_combos())
        if py == asp_set:
            print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        else:
            ok = False
            print("MISMATCH in combo parity:")
            if asp_set - py:
                print("  only in ASP:", sorted(asp_set - py))
            if py - asp_set:
                print("  only in Python:", sorted(py - asp_set))
    except Exception:
        ok = False
        traceback.print_exc()

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate() produced a story.")
        _ = sample.to_json()
    except Exception:
        ok = False
        traceback.print_exc()

    return 0 if ok else 1


def _pick_name(rng: random.Random, typ: str, avoid: str = "") -> str:
    pool = BOY_NAMES if typ == "boy" else GIRL_NAMES
    opts = [n for n in pool if n != avoid]
    return rng.choice(opts)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.craving not in CRAVINGS:
        raise StoryError(f"Unknown craving: {params.craving}")
    if params.share_move not in SHARES:
        raise StoryError(f"Unknown share move: {params.share_move}")
    world = tell(
        SETTINGS[params.setting],
        CRAVINGS[params.craving],
        SHARES[params.share_move],
        params.hero,
        params.hero_type,
        params.mate,
        params.mate_type,
        params.leader,
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
    StoryParams(setting="harbor_pizzeria", craving="pepper_pies", hero="Milo", hero_type="boy", mate="Nina", mate_type="girl", leader="captain", share_move="split_slice"),
    StoryParams(setting="dockside_pizzeria", craving="golden_slices", hero="Ivy", hero_type="girl", mate="Kai", mate_type="boy", leader="mate", share_move="share_jobs"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.craving is None or c[1] == args.craving)
              and (args.share_move is None or c[2] == args.share_move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, craving, share_move = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    mate_type = args.mate_type or ("girl" if hero_type == "boy" else "boy")
    hero = args.hero or _pick_name(rng, hero_type)
    mate = args.mate or _pick_name(rng, mate_type, avoid=hero)
    leader = args.leader or rng.choice(LEADER_TYPES)
    return StoryParams(setting=setting, craving=craving, hero=hero, hero_type=hero_type, mate=mate, mate_type=mate_type, leader=leader, share_move=share_move)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, m) for s in SETTINGS for c in CRAVINGS for m in SHARES]


def build_seeded_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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
    return samples


def build_all_samples() -> list[StorySample]:
    return [generate(p) for p in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    samples = build_all_samples() if args.all else build_seeded_samples(args)

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
            header = f"### {p.hero} & {p.mate}: {p.craving} in {p.setting} (sharing: {p.share_move})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
