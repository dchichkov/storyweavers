#!/usr/bin/env python3
"""
storyworlds/worlds/flap_american_children_s_museum_conflict_quest.py
====================================================================

A small classical story world in a children's museum, told in a mythic style.

Seed premise:
- a child comes to a children's museum on a quest
- there is a conflict over a flap on an American exhibit
- the turn is a wise compromise that keeps the exhibit safe while completing the quest

The world is intentionally tiny and constraint-checked: the child only gets a
story when the quest is meaningful, the conflict is real, and the resolution
actually changes the simulated state.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str = "the children's museum"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    consequence: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        for quest in QUESTS.values():
            if hero.meters[quest.id] < THRESHOLD:
                continue
            for item in world.worn_items(hero):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(hero, item.region):
                    continue
                sig = ("soil", hero.id, item.id, quest.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["scuffed"] += 1
                item.meters[quest.danger] += 1
                out.append(f"{hero.pronoun('possessive').capitalize()} {item.label} grew scuffed in the quest.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["warning"] < THRESHOLD or hero.memes["want"] < THRESHOLD:
            continue
        sig = ("conflict", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("soil", "physical", _r_soil),
    Rule("conflict", "social", _r_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.danger in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_world(world: World, hero: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"damaged": bool(prize and prize.meters["scuffed"] >= THRESHOLD)}


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in world.setting.affords:
        return
    world.zone = set(quest.zone)
    hero.meters[quest.id] += 1
    hero.memes["hope"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a little {trait} {hero.type} who came to the children's museum like a small pilgrim.")
    world.say("The halls were bright, and every display seemed to wait for a question.")


def loves_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["love"] += 1
    world.say(f"{hero.id} loved {quest.gerund}, for the quest felt like a story hidden inside the museum.")


def show_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"On a high shelf in the gallery, {hero.id}'s {parent.label} had given {hero.pronoun('object')} "
        f"{prize.phrase}, a treasure fit for a careful heart."
    )
    prize.worn_by = hero.id
    hero.memes["love_prize"] += 1


def arrive(world: World, hero: Entity, parent: Entity, quest: Quest) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} entered {world.setting.place}.")
    world.say("There, a tiny door with a flap stood near an American exhibit of maps, flags, and brave little journeys.")


def wants(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["want"] += 1
    world.say(f"{hero.id} wanted to {quest.verb}, but the flap looked fragile, like a dragon's eyelid made of paper.")


def warn(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity) -> bool:
    pred = predict_world(world, hero, quest, prize.id)
    if not pred["damaged"]:
        return False
    hero.memes["warning"] += 1
    world.facts["predicted_damage"] = True
    world.say(f"\"If you {quest.verb}, your {prize.label} may be {quest.consequence},\" {parent.label} said.")
    return True


def defy(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["stubborn"] += 1
    world.say(f"{hero.id} still felt the pull of the quest and reached toward the flap.")


def grab(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["held"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {hero.pronoun('possessive')} {parent.label} gently held {hero.pronoun('possessive')} hand and would not let the quest become a ruin.")


def compromise(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity) -> Optional[Gear]:
    gear = select_gear(quest, prize)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    g.worn_by = hero.id
    if predict_world(world, hero, quest, prize.id)["damaged"]:
        del world.entities[g.id]
        return None
    world.say(f"{parent.label} found a wiser path: {gear.prep}.")
    return gear


def accept(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity, gear: Gear) -> None:
    hero.memes["hope"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} smiled, and the two of them {gear.tail}.")
    world.say(
        f"At last {hero.id} was {quest.gerund}, the flap remained whole, "
        f"and the American exhibit shone like a little kingdom kept safe."
    )


def tell(
    setting: Setting,
    quest: Quest,
    prize_cfg: Prize,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious", "bold"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="guide"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    intro(world, hero)
    loves_quest(world, hero, quest)
    show_prize(world, parent, hero, prize)
    world.para()
    arrive(world, hero, parent, quest)
    wants(world, hero, quest)
    warn(world, parent, hero, quest, prize)
    defy(world, hero, quest)
    grab(world, parent, hero)
    world.para()
    gear = compromise(world, parent, hero, quest, prize)
    if gear:
        accept(world, parent, hero, quest, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, quest=quest, setting=setting, gear=gear, resolved=gear is not None)
    return world


SETTINGS = {
    "museum": Setting(place="the children's museum", indoor=True, affords={"flap_quest", "american_quest"}),
}

QUESTS = {
    "flap_quest": Quest(
        id="flap_quest",
        verb="open the flap",
        gerund="opening the flap",
        rush="run to the flap",
        danger="torn",
        consequence="torn",
        zone={"torso"},
        keyword="flap",
        tags={"flap", "museum", "quest"},
    ),
    "american_quest": Quest(
        id="american_quest",
        verb="follow the American map",
        gerund="following the American map",
        rush="dash toward the American map",
        danger="smudged",
        consequence="smudged",
        zone={"torso"},
        keyword="american",
        tags={"american", "museum", "quest"},
    ),
}

GEAR = [
    Gear(
        id="soft_gloves",
        label="soft felt gloves",
        covers={"torso"},
        guards={"torn", "smudged"},
        prep="wear soft felt gloves first",
        tail="walked on with soft felt gloves on",
        plural=True,
    ),
    Gear(
        id="library_tab",
        label="a library tab",
        covers={"torso"},
        guards={"torn"},
        prep="place a library tab on the flap first",
        tail="carried the quest with a library tab",
    ),
    Gear(
        id="museum_clip",
        label="a museum clip",
        covers={"torso"},
        guards={"torn", "smudged"},
        prep="use a museum clip first",
        tail="went softly onward with the museum clip",
    ),
]

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright little cape", type="cape", region="torso"),
    "card": Prize(label="card", phrase="a shiny museum card", type="card", region="torso"),
    "badge": Prize(label="badge", phrase="a paper badge of honor", type="badge", region="torso"),
}

NAMES_GIRL = ["Mira", "Luna", "Tessa", "Ivy", "Nora"]
NAMES_BOY = ["Owen", "Theo", "Ezra", "Kai", "Miles"]
TRAITS = ["curious", "brave", "gentle", "bold", "hopeful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = QUESTS[qid]
            for pid, prize in PRIZES.items():
                if quest_at_risk(q, prize) and select_gear(q, prize):
                    combos.append((place, qid, pid))
    return combos


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "flap": [("What is a flap?", "A flap is a part that can lift or fold over something, like a little door." )],
    "american": [("What does American mean?", "American can mean something connected to the United States, like a flag, map, or story from there.")],
    "museum": [("What is a museum?", "A museum is a place where people keep and show interesting things so others can learn from them.")],
    "quest": [("What is a quest?", "A quest is a search or journey to find something important or solve a problem.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, quest, prize = f["hero"], f["parent"], f["quest"], f["prize"]
    return [
        f'Write a myth-like story for a child in a children's museum that includes the word "{quest.keyword}".',
        f"Tell a small heroic tale where {hero.id} wants to {quest.verb} but {parent.label} fears for the {prize.label}.",
        f"Write a gentle story with a conflict and a quest in a children's museum, and end with a safe compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, quest, prize = f["hero"], f["parent"], f["quest"], f["prize"]
    qa = [
        QAItem(
            question=f"Who went to the children's museum on the quest?",
            answer=f"{hero.id} went to the children's museum with {hero.pronoun('possessive')} {parent.label} on a small quest.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the flap or the American exhibit?",
            answer=f"{hero.id} wanted to {quest.verb}, because the quest felt important and shining.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because if {hero.id} kept going, the {prize.label} could become {quest.consequence}.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the story end safely?",
            answer=f"They used {gear.label} first, so {hero.id} could finish {quest.gerund} without harming the flap or the exhibit.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and brave, because the quest was completed and the fear was gone.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    out: list[QAItem] = []
    for key in ["flap", "american", "museum", "quest"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="museum", quest="flap_quest", prize="cape", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="museum", quest="american_quest", prize="card", name="Owen", gender="boy", parent="father", trait="brave"),
    StoryParams(place="museum", quest="flap_quest", prize="badge", name="Tessa", gender="girl", parent="mother", trait="hopeful"),
]


def explain_rejection(quest: Quest, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not quest_at_risk(quest, prize):
        return f"(No story: the {prize.label} is not in danger from {quest.gerund}, so the conflict would be fake.)"
    if not select_gear(quest, prize):
        return f"(No story: nothing in the gear catalog can protect {noun} from {quest.gerund}.)"
    return "(No story: this option does not make a meaningful mythic conflict.)"


ASP_RULES = r"""
quest_at_risk(Q,P) :- zone(Q,R), worn_on(P,R).
compatible(G,Q,P) :- quest_at_risk(Q,P), danger(Q,D), guards(G,D), covers(G,R), worn_on(P,R).
has_fix(Q,P) :- compatible(_,Q,P).
valid(Place,Q,P) :- affords(Place,Q), quest_at_risk(Q,P), has_fix(Q,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("danger", qid, q.danger))
        for r in sorted(q.zone):
            lines.append(asp.fact("zone", qid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for d in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
    ap = argparse.ArgumentParser(description="Mythic children's museum conflict-quest world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
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
    if args.quest and args.prize:
        q, p = QUESTS[args.quest], PRIZES[args.prize]
        if not (quest_at_risk(q, p) and select_gear(q, p)):
            raise StoryError(explain_rejection(q, p))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        QUESTS[params.quest],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait, "stubborn"],
        params.parent,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, prize) combos:")
        for place, quest, prize in combos:
            print(f"  {place:22} {quest:16} {prize}")
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
