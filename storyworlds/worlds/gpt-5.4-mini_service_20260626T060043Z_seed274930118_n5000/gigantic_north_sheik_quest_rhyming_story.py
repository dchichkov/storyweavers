#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gigantic_north_sheik_quest_rhyming_story.py
================================================================================================

A tiny, self-contained storyworld for a rhyming quest tale: a sheik, a northward
journey, and one gigantic thing to fetch.

Seed-tale premise:
---
A small child and a kind sheik hear of a gigantic treasure hidden far to the
north. They set out on a quest with a map, a lantern, and a brave song. The way
is cold and windy, so they must choose whether to push on, turn back, or add the
right gear. In the end, they find the treasure and return with a cheerful rhyme.

This script models that premise as a small world with physical meters and
emotional memes:
- meters: cold, tired, lost, bright, carried, safe
- memes: hope, worry, pride, joy, trust

The narration is intentionally rhyme-forward and child-facing.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "sheik"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    coldness: float
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    resolution: str
    route: str
    goal: str
    keyword: str = "Quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    carried: bool = True
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route: str = ""
        self.goal: str = ""

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.route = self.route
        clone.goal = self.goal
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if world.setting.coldness < THRESHOLD:
            continue
        if ent.meters.get("warm", 0.0) >= THRESHOLD:
            continue
        sig = ("cold", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meter(ent, "cold")
        _add_meter(ent, "tired")
        _add_meme(ent, "worry")
        out.append(f"The north wind nipped at {ent.id}, and {ent.pronoun('possessive')} nose went red and bright.")
    return out


def _r_lantern(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.meters.get("dark", 0.0) < THRESHOLD:
            continue
        if any(item.id == "lantern" and item.carried_by == ent.id for item in world.entities.values()):
            sig = ("bright", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["bright"] = ent.meters.get("bright", 0.0) + 1
            out.append(f"A lantern made a little bright, so {ent.id} could keep a merry sight.")
    return out


def _r_goal_found(world: World) -> list[str]:
    out: list[str] = []
    if world.goal != "north_star_harp":
        return out
    hero = world.entities.get("Hero")
    sheik = world.entities.get("Sheik")
    if not hero or not sheik:
        return out
    if hero.meters.get("search", 0.0) < THRESHOLD:
        return out
    if sheik.meters.get("search", 0.0) < THRESHOLD:
        return out
    sig = ("found", world.goal)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize = world.entities.get("Prize")
    if prize:
        prize.carried_by = hero.id
        _add_meter(prize, "carried")
    _add_meme(hero, "joy")
    _add_meme(sheik, "pride")
    out.append("At last they found the gigantic north star harp, all silver and neat.")
    return out


CAUSAL_RULES = [_r_cold, _r_lantern, _r_goal_found]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} {b}"


def intro_line(hero: Entity, sheik: Entity, setting: Setting) -> str:
    return (
        f"{hero.id} met the sheik with a smile so sleek, and they set out north on a quest that week."
    )


def setup_line(hero: Entity, sheik: Entity, prize: Entity) -> str:
    return (
        f"They sought a gigantic prize so bright and grand: {prize.phrase}, a wonder in the sand."
    )


def quest_line(hero: Entity, sheik: Entity, quest: Quest) -> str:
    return (
        f"They followed the {quest.route} with steady feet, singing soft little lines to keep the beat."
    )


def warning_line(hero: Entity, sheik: Entity, quest: Quest) -> str:
    return (
        f"But the north grew cold, and the wind grew keen; the path was icy, slick, and mean."
    )


def choose_line(hero: Entity, sheik: Entity, gear: Optional[Gear], quest: Quest) -> str:
    if gear is None:
        return f"They hugged their cloaks and hoped to cope, but hope alone was not enough for the slope."
    return f"The sheik saw the shiver and chose the {gear.label}; that warm little plan made the journey jive."


def end_line(hero: Entity, sheik: Entity, prize: Entity, quest: Quest, gear: Optional[Gear]) -> str:
    if gear is None:
        return f"So they turned back home, with cheeks a bit blue, and promised a wiser quest tomorrow too."
    return (
        f"They reached the prize, then headed home in springy stride; the gigantic north star harp rode safe inside."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize,
         hero_name: str = "Ari", hero_type: str = "child",
         sheik_name: str = "Sheik", seed: Optional[int] = None) -> World:
    world = World(setting)
    world.route = quest.route
    world.goal = quest.goal
    world.setting = setting

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["small", "brave"],
        meters={"search": 0.0, "tired": 0.0},
        memes={"hope": 1.0, "joy": 0.0, "worry": 0.0},
    ))
    sheik = world.add(Entity(
        id=sheik_name,
        kind="character",
        type="sheik",
        traits=["kind", "wise"],
        meters={"search": 0.0, "tired": 0.0},
        memes={"hope": 1.0, "pride": 0.0, "trust": 1.0},
    ))
    prize = world.add(Entity(
        id="Prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        carried_by=None,
        plural=prize_cfg.plural,
        meters={"carried": 0.0},
    ))

    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase="a small lantern",
        carried_by=hero.id,
        meters={"dark": 0.0},
    ))
    cloak = world.add(Entity(
        id="cloak",
        kind="thing",
        type="cloak",
        label="warm cloak",
        phrase="a warm cloak",
        carried_by=sheik.id,
        meters={"warm": 1.0},
    ))

    world.say(intro_line(hero, sheik, setting))
    world.say(setup_line(hero, sheik, prize))
    world.say(quest_line(hero, sheik, quest))
    world.para()

    _add_meme(hero, "hope")
    _add_meme(sheik, "hope")
    _add_meter(hero, "search")
    _add_meter(sheik, "search")
    world.say(warning_line(hero, sheik, quest))
    _add_meter(hero, "dark")
    propagate(world, narrate=True)
    world.say(choose_line(hero, sheik, GEAR["cloak"] if setting.coldness >= THRESHOLD else None, quest))
    if setting.coldness >= THRESHOLD:
        hero.meters["warm"] = 1.0

    gear = None
    if setting.coldness >= THRESHOLD:
        gear = world.add(Entity(
            id="travel_cloak",
            kind="thing",
            type="cloak",
            label="travel cloak",
            phrase="a travel cloak",
            carried_by=sheik.id,
            meters={"warm": 1.0},
        ))
        sheik.memes["trust"] += 1.0
        hero.meters["warm"] = 1.0
        _add_meter(hero, "search")
        _add_meter(sheik, "search")
        propagate(world, narrate=True)

    if setting.coldness >= THRESHOLD:
        world.para()
        world.say(end_line(hero, sheik, prize, quest, gear))
    else:
        world.para()
        world.say(f"The quest stayed light and bright, and they found their way by day and by night.")
        world.say(f"With a clap and a laugh, they came right back home, and the north breeze whistled through every comb.")

    world.facts.update(
        hero=hero,
        sheik=sheik,
        prize=prize,
        lantern=lantern,
        cloak=cloak,
        gear=gear,
        quest=quest,
        setting=setting,
        resolved=bool(gear),
    )
    return world


SETTINGS = {
    "camp": Setting(place="the desert camp", coldness=0.0, affords={"quest"}),
    "north_pass": Setting(place="the north pass", coldness=1.0, affords={"quest"}),
    "ice_dune": Setting(place="the ice dune", coldness=2.0, affords={"quest"}),
}

QUESTS = {
    "north_star_harp": Quest(
        id="north_star_harp",
        verb="go on a quest for the gigantic north star harp",
        gerund="going north on a quest",
        rush="race toward the north glow",
        danger="cold wind",
        resolution="warm cloak",
        route="north trail",
        goal="north_star_harp",
        keyword="Quest",
        tags={"quest", "north", "gigantic", "sheik"},
    ),
    "north_bell": Quest(
        id="north_bell",
        verb="go on a quest for the gigantic north bell",
        gerund="walking north on a quest",
        rush="hurry toward the north hill",
        danger="icy stones",
        resolution="warm cloak",
        route="north road",
        goal="north_bell",
        keyword="Quest",
        tags={"quest", "north", "gigantic", "sheik"},
    ),
}

PRIZES = {
    "harp": Prize(
        label="north star harp",
        phrase="the gigantic north star harp",
        type="harp",
        carried=True,
    ),
    "bell": Prize(
        label="north bell",
        phrase="the gigantic north bell",
        type="bell",
        carried=True,
    ),
}

GEAR = {
    "cloak": Gear(
        id="cloak",
        label="warm cloak",
        phrase="a warm cloak",
        guards={"cold"},
        prep="put on a warm cloak",
        tail="put on the warm cloak and kept going",
    )
}

NAMES = ["Ari", "Mira", "Lina", "Omar", "Noa", "Sami"]
SHEIK_NAMES = ["Sheik", "Sheik Noor", "Sheik Rami", "Sheik Zayd"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    prize: str
    name: str
    sheik: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for q in QUESTS:
            for p in PRIZES:
                combos.append((s, q, p))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest: Quest = f["quest"]
    return [
        f'Write a short rhyming story for a child about a {quest.keyword.lower()} and a northward quest.',
        f"Tell a gentle rhyme where {f['hero'].id} and {f['sheik'].id} travel north to find {f['prize'].phrase}.",
        f'Write a simple story that uses the words "gigantic", "north", and "sheik" and ends happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sheik: Entity = f["sheik"]
    prize: Entity = f["prize"]
    quest: Quest = f["quest"]
    setting: Setting = f["setting"]

    qa = [
        QAItem(
            question=f"Who went on the quest in the story?",
            answer=f"{hero.id} and {sheik.id} went on a northward quest together.",
        ),
        QAItem(
            question=f"What gigantic thing were they trying to find?",
            answer=f"They were trying to find {prize.phrase}.",
        ),
        QAItem(
            question=f"Where did the quest lead them?",
            answer=f"It led them north, toward {setting.place}.",
        ),
        QAItem(
            question=f"Why did the trip feel hard?",
            answer=f"It felt hard because the north wind was cold and the path was sharp with chilly air.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="How did they keep going when the north got cold?",
                answer="They put on a warm cloak, which helped them stay cozy and kept the quest going.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a long search or journey to find something important or to finish a special goal.",
        ),
        QAItem(
            question="What does north mean?",
            answer="North is one direction on a map or compass; people use it to find their way.",
        ),
        QAItem(
            question="Who is a sheik?",
            answer="A sheik is a leader or respected person in some places, often someone people listen to and trust.",
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, quest: Quest, prize: Prize) -> str:
    return "(No story: the requested mix does not fit this small quest world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny rhyming quest storyworld with a sheik and a northward journey."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sheik", choices=SHEIK_NAMES)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid quest combinations exist.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    quest = args.quest or rng.choice(sorted(QUESTS))
    prize = args.prize or rng.choice(sorted(PRIZES))
    if (setting, quest, prize) not in combos:
        raise StoryError(explain_rejection(SETTINGS[setting], QUESTS[quest], PRIZES[prize]))
    name = args.name or rng.choice(NAMES)
    sheik = args.sheik or rng.choice(SHEIK_NAMES)
    return StoryParams(setting=setting, quest=quest, prize=prize, name=name, sheik=sheik)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        PRIZES[params.prize],
        hero_name=params.name,
        sheik_name=params.sheik,
        seed=params.seed,
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


ASP_RULES = r"""
quest_story(S,Q,P) :- setting(S), quest(Q), prize(P).
northy(Q) :- quest(Q), tags(Q,north).
gigantic(Q) :- quest(Q), tags(Q,gigantic).
sheik_story(Q) :- quest(Q), tags(Q,sheik).
valid_story(S,Q,P) :- quest_story(S,Q,P), northy(Q), gigantic(Q), sheik_story(Q).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("tags", qid, t))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(setting="north_pass", quest="north_star_harp", prize="harp", name="Ari", sheik="Sheik Noor"),
    StoryParams(setting="ice_dune", quest="north_bell", prize="bell", name="Mira", sheik="Sheik Rami"),
    StoryParams(setting="camp", quest="north_star_harp", prize="harp", name="Noa", sheik="Sheik Zayd"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print(" ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
