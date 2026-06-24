#!/usr/bin/env python3
"""
storyworlds/worlds/chump_queer_proper_inner_monologue_quest_adventure.py
=======================================================================

A small standalone story world for an Adventure-style quest with inner
monologue, a proper plan, and a gentle queer-coded friendship/identity beat.

Premise:
- A child-sized hero is sent on a quest to recover a lost badge from a garden
  maze, treehouse trail, or museum hall.
- The hero starts feeling like a chump because the path seems too hard.
- Their inner monologue argues with fear, then settles on a proper plan.
- A helpful queer friend, sibling, or guide joins in with clever map-reading,
  and the quest ends with a small victory image that proves the change.

The prose is state-driven: courage, doubt, gear, location, and ownership all
shape what gets narrated. The world model tracks physical meters and emotional
memes, and a small ASP twin mirrors the reasonableness gate.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    setting: str
    paths: list[str] = field(default_factory=list)
    affordances: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    location: str
    risk: str
    region: str
    plural: bool = False


@dataclass
class Companion:
    id: str
    label: str
    role: str
    traits: list[str] = field(default_factory=list)
    queer: bool = False
    helpful: bool = True
    clue: str = ""
    tool: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path: str = ""

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.path = self.path
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_confidence(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.memes["doubt"] < THRESHOLD:
            continue
        sig = ("confidence", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.memes["plan"] >= THRESHOLD:
            e.memes["courage"] += 1
            out.append(f"{e.id} remembered the plan and stood a little straighter.")
    return out


def _r_find_item(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    item = world.get("quest_item")
    if hero.meters["searched"] >= THRESHOLD and world.path == item.location:
        sig = ("find", item.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        item.meters["found"] += 1
        out.append(f"The {item.label} was right there, waiting in the {world.place.label}.")
    return out


CAUSAL_RULES = [
    Rule("confidence", "mind", _r_confidence),
    Rule("find", "world", _r_find_item),
]


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


def quest_at_risk(place: Place, item: QuestItem) -> bool:
    return item.region in place.affordances


def select_companion(item: QuestItem) -> Companion:
    for c in COMPANIONS:
        if c.helpful and item.risk in c.clue:
            return c
    return COMPANIONS[0]


def inner_monologue(hero: Entity, item: QuestItem, companion: Companion, place: Place) -> list[str]:
    return [
        f"{hero.id} thought, I feel like a chump if I can't do this quest.",
        f"But maybe a proper plan would help, and {companion.id} might know the safest way through {place.label}.",
        f"If I keep going, I can still find {item.label} and look brave in my own way.",
    ]


def predict_success(world: World, item_id: str) -> dict:
    sim = world.copy()
    sim.get("hero").meters["searched"] += 1
    propagate(sim, narrate=False)
    item = sim.get(item_id)
    return {"found": item.meters["found"] >= THRESHOLD}


def build_hero(world: World, name: str, gender: str, trait: str) -> Entity:
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=[trait, "curious"]))
    hero.memes["doubt"] = 1.0
    hero.memes["courage"] = 0.0
    hero.memes["plan"] = 0.0
    return hero


def setup(world: World, hero: Entity, companion: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} arrived at {world.place.label} on a proper little quest."
    )
    world.say(
        f"{hero.id} had to find {item.phrase}, but the path looked tricky."
    )
    world.say(
        f"{companion.id} came along with a {companion.label} grin and a useful {companion.tool}."
    )


def worry(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["doubt"] += 1
    world.say(
        f"{hero.id} stared at the trail and felt like a chump for a moment."
    )
    for line in inner_monologue(hero, item, world.get("companion").__dict__.get("companion_obj"), world.place):
        world.say(line)


def choose_plan(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["plan"] += 1
    hero.meters["searched"] += 1
    world.path = world.facts["path"]
    world.say(
        f"{companion.id} pointed to {world.facts['path_phrase']} and said, "
        f'"Stay proper. Start there, then follow the chalk marks."'
    )
    world.say(
        f"{hero.id} listened, took a breath, and followed the plan."
    )
    propagate(world)


def resolve(world: World, hero: Entity, companion: Entity, item: Entity) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"At last {hero.id} found {item.label} tucked where the map said it would be."
    )
    world.say(
        f"{hero.id} held it up while {companion.id} laughed and said the quest had been solved properly."
    )
    world.say(
        f"The chump feeling was gone; in its place was a small, bright kind of pride."
    )


def tell(place: Place, item_cfg: QuestItem, companion_cfg: Companion,
         hero_name: str = "June", hero_gender: str = "girl",
         trait: str = "brave") -> World:
    world = World(place)
    world.facts["path"] = place.paths[0] if place.paths else "the main path"
    world.facts["path_phrase"] = f"{world.facts['path']}"
    hero = build_hero(world, hero_name, hero_gender, trait)
    companion = world.add(Entity(id="companion", kind="character", type="girl" if companion_cfg.queer else "boy",
                                 label=companion_cfg.label, role=companion_cfg.role,
                                 traits=companion_cfg.traits))
    companion.__dict__["companion_obj"] = companion_cfg
    item = world.add(Entity(id="quest_item", type="thing", label=item_cfg.label, phrase=item_cfg.phrase))
    world.facts.update(hero=hero, companion=companion, quest_item=item, companion_cfg=companion_cfg)

    setup(world, hero, companion, item)
    world.para()
    worry(world, hero, item)
    hero.memes["plan"] += 1
    choose_plan(world, hero, companion)
    if predict_success(world, item.id)["found"]:
        world.para()
        resolve(world, hero, companion, item)

    world.facts["outcome"] = "found" if item.meters["found"] >= THRESHOLD else "missed"
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="the lantern garden",
        setting="a bright maze of hedges and stone paths",
        paths=["the chalk path", "the narrow archway", "the stone bridge"],
        affordances={"path", "bridge"},
    ),
    "treehouse": Place(
        id="treehouse",
        label="the treehouse trail",
        setting="a rope ladder, wooden steps, and a windy lookout",
        paths=["the ladder", "the rope rail", "the plank walk"],
        affordances={"ladder", "walk"},
    ),
    "museum": Place(
        id="museum",
        label="the quiet museum hall",
        setting="glass cases, velvet ropes, and a map of old rooms",
        paths=["the map desk", "the side corridor", "the painted arch"],
        affordances={"corridor", "arch"},
    ),
}

QUEST_ITEMS = {
    "badge": QuestItem(
        id="badge",
        label="lost badge",
        phrase="a shiny lost badge",
        location="the chalk path",
        risk="hedge",
        region="path",
    ),
    "key": QuestItem(
        id="key",
        label="brass key",
        phrase="a small brass key",
        location="the rope rail",
        risk="rope",
        region="walk",
    ),
    "ticket": QuestItem(
        id="ticket",
        label="paper ticket",
        phrase="a proper old ticket",
        location="the side corridor",
        risk="glass",
        region="corridor",
    ),
}

COMPANIONS = [
    Companion(id="Rae", label="Rae", role="guide", traits=["queer", "calm"], queer=True, clue="path", tool="map"),
    Companion(id="Milo", label="Milo", role="sibling", traits=["cheerful", "queer"], queer=True, clue="walk", tool="lantern"),
    Companion(id="Nia", label="Nia", role="friend", traits=["proper", "kind"], queer=False, clue="corridor", tool="chalk"),
]

GIRL_NAMES = ["June", "Ava", "Mina", "Lia", "Iris", "Pia"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Eli", "Noah", "Max"]
TRAITS = ["curious", "proper", "thoughtful", "bold", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for item_id, item in QUEST_ITEMS.items():
            if quest_at_risk(place, item):
                combos.append((place_id, item_id))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    companion: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an Adventure-style story about {f["hero"].id} on a quest in {f["place"].label}.',
        f"Tell a gentle adventure where {f['hero'].id} feels like a chump, then uses a proper plan with {f['companion_cfg'].label}.",
        f'Write a simple inner-monologue quest story that includes the word "queer" in a kind, natural way and ends with a found object.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, comp, item, place = f["hero"], f["companion"], f["quest_item"], f["place"]
    return [
        QAItem(
            question=f"Who is the story about on the quest at {place.label}?",
            answer=f"It is about {hero.id}, who went on a quest at {place.label} with {comp.id} to find {item.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel like a chump at first?",
            answer=f"{hero.id} felt unsure because the path looked hard, but the inner monologue helped {hero.pronoun('object')} keep going.",
        ),
        QAItem(
            question=f"How did {comp.id} help {hero.id}?",
            answer=f"{comp.id} gave a proper plan, pointed out the right path, and stayed beside {hero.id} until the {item.label} was found.",
        ),
        QAItem(
            question=f"What changed by the end of the quest?",
            answer=f"{hero.id} stopped feeling like a chump and felt proud after finding {item.label} with {comp.id}'s help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something, solve a problem, or reach an important goal.",
        ),
        QAItem(
            question="What does inner monologue mean?",
            answer="Inner monologue means the private thoughts a character says to themselves inside their head.",
        ),
        QAItem(
            question="What does queer mean in a friendly story?",
            answer="Queer can describe a person whose gender or love story is not the usual one. In a kind story, it is just part of who someone is.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_risk(P, I) :- place(P), item(I), region(I, R), affordance(P, R).
found(I) :- hero_search(S), location(I, S), quest_risk(_, I).
proper_plan(H) :- plan(H), courage(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affordance", pid, a))
    for iid, i in QUEST_ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("location", iid, i.location))
        lines.append(asp.fact("region", iid, i.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_risk/2."))
    return sorted(set(asp.atoms(model, "quest_risk")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos().")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style quest storyworld with inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=QUEST_ITEMS)
    ap.add_argument("--companion", choices=[c.id for c in COMPANIONS])
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
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item = rng.choice(sorted(combos))
    companion = args.companion or rng.choice([c.id for c in COMPANIONS])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, companion=companion, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    item_cfg = QUEST_ITEMS[params.item]
    comp_cfg = next(c for c in COMPANIONS if c.id == params.companion)
    world = tell(place, item_cfg, comp_cfg, params.name, params.gender, params.trait)
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
    StoryParams(place="garden", item="badge", companion="Rae", name="June", gender="girl", trait="curious"),
    StoryParams(place="treehouse", item="key", companion="Milo", name="Finn", gender="boy", trait="proper"),
    StoryParams(place="museum", item="ticket", companion="Nia", name="Ava", gender="girl", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show quest_risk/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, i in asp_valid_combos():
            print(f"  {p} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
