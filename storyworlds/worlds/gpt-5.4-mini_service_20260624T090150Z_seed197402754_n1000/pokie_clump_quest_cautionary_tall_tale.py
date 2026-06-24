#!/usr/bin/env python3
"""
Storyworld: Pokie Clump Quest
==============================

A small cautionary tall-tale storyworld about a child, a pokie clump,
and a quest that only succeeds when the hero listens to warnings and
uses the right tools.

The world is intentionally simple:
- a hero wants to fetch the pokie clump from a far place
- the route is full of prickly trouble
- ignoring a warning makes the quest more painful
- a helper offers a safe fix, and the ending proves the choice changed

This file is standalone and uses only the standard library plus the
shared result containers from storyworlds/results.py.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    zone: set[str]
    caution: str
    keyword: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_poke(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("poked", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            sig = ("poke", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["punctured"] = item.meters.get("punctured", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} snagged on the pokie clump.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("punctured", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] = caretaker.memes.get("worry", 0) + 1
        out.append(f"That gave {caretaker.label_word} a worried frown.")
    return out


def _r_warning(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("warned", 0) < THRESHOLD or actor.memes.get("stubborn", 0) < THRESHOLD:
            continue
        sig = ("trouble", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trouble"] = actor.memes.get("trouble", 0) + 1
        out.append("__trouble__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_poke, _r_worry, _r_warning):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__trouble__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.hazard in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(actor.id), quest, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "punctured": prize.meters.get("punctured", 0) >= THRESHOLD,
        "worry": sum(e.memes.get("worry", 0) for e in sim.characters()),
    }


def _do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} cannot host the {quest.id} quest.)")
    world.zone = set(quest.zone)
    actor.meters["poked"] = actor.meters.get("poked", 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who liked grand errands and long roads."
    )


def wants_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {quest.verb}, "
        f"and everyone in town called it a pokie clump quest."
    )


def warn(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity) -> bool:
    pred = predict_mess(world, hero, quest, prize.id)
    if not pred["punctured"]:
        return False
    hero.memes["warned"] = hero.memes.get("warned", 0) + 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"Careful," {parent.label_word} said. "That pokie clump can snag a sleeve '
        f"and leave a heart in a hurry.""
    )
    return True


def ignore_warning(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    world.say(
        f"{hero.id} heard the warning, but {hero.pronoun('possessive')} feet were already itching forward."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {quest.rush},")
    

def conflict(world: World, parent: Entity, hero: Entity, quest: Quest) -> None:
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} caught {hero.pronoun('possessive')} sleeve and said, "
        f'"A wise traveler does not dance through pokie clumps with bare hands."'
    )


def compromise(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(quest, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, quest, prize.id)["punctured"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{parent.label_word} smiled and said, "
        f'"How about we {gear_def.prep} and still go after the pokie clump?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    hero.memes["stubborn"] = 0.0
    world.say(
        f"{hero.id}'s face lit up, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}."
    )
    world.say(
        f"Together they {gear_def.tail}. Soon {hero.id} was {quest.gerund}, "
        f"{prize.label} stayed safe, and the pokie clump came home in a careful bundle."
    )


def tell(
    setting: Setting,
    quest: Quest,
    prize_cfg: Prize,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    wants_quest(world, hero, quest)
    world.say(f"The prize was {prize.phrase}, and it had to be brought back from the far end of town.")
    world.para()
    world.say(f"One day, {hero.id} headed for {world.setting.place}.")
    world.say(f"The path there was full of {quest.caution}, and the pokie clump waited in a thorny tangle.")
    warn(world, parent, hero, quest, prize)
    ignore_warning(world, hero, quest)
    conflict(world, parent, hero, quest)
    world.para()
    gear_def = compromise(world, parent, hero, quest, prize)
    if gear_def:
        accept(world, parent, hero, quest, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        quest=quest,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
        warned=hero.memes.get("warned", 0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "briar_road": Setting(place="the briar road", affords={"quest"}),
    "hill_lane": Setting(place="the hill lane", affords={"quest"}),
    "orchard_edge": Setting(place="the orchard edge", affords={"quest"}),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        verb="fetch the pokie clump",
        gerund="fetching the pokie clump",
        rush="dash into the thorn patch",
        hazard="pokie",
        zone={"arms", "hands"},
        caution="small prickles and sneaky thorns",
        keyword="pokie",
        tags={"pokie", "clump", "quest", "cautionary", "tall tale"},
    ),
}

PRIZES = {
    "bundle": Prize(
        label="bundle",
        phrase="a puffed-up bundle of letters",
        type="bundle",
        region="hands",
        plural=False,
    )
}

GEAR = [
    Gear(
        id="gloves",
        label="thick work gloves",
        covers={"hands"},
        guards={"pokie"},
        prep="put on thick work gloves first",
        tail="went back with thick work gloves on",
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tessa", "Penny"]
BOY_NAMES = ["Owen", "Jasper", "Theo", "Eli", "Ben"]
TRAITS = ["brave", "curious", "stubborn", "bright-eyed", "spirited"]


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
    "pokie": [
        ("What does pokie mean?", "Pokie means sharp or prickly, like something that can poke your skin."),
    ],
    "clump": [
        ("What is a clump?", "A clump is a small bunch of things stuck or gathered together."),
    ],
    "quest": [
        ("What is a quest?", "A quest is a special journey to find or do something important."),
    ],
    "cautionary": [
        ("What does cautionary mean?", "Cautionary means it gives a warning so someone can stay safe."),
    ],
    "tall tale": [
        ("What is a tall tale?", "A tall tale is a story with big, lively details that makes ordinary things sound grand."),
    ],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = QUESTS[qid]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(quest, prize) and select_gear(quest, prize):
                    combos.append((place, qid, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, quest, prize = f["hero"], f["parent"], f["quest"], f["prize"]
    return [
        f'Write a cautionary tall tale about a child named {hero.id} who goes on a pokie clump quest.',
        f"Tell a story where {hero.id} wants to {quest.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f'Write a child-friendly tall tale that includes the words "pokie" and "clump" and ends with a safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, quest, prize = f["hero"], f["parent"], f["quest"], f["prize"]
    qa = [
        QAItem(
            question=f"Who wanted to go on the pokie clump quest?",
            answer=f"{hero.id} wanted to go on the pokie clump quest, and {hero.pronoun('possessive')} {parent.label_word} watched closely.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} warn {hero.id} about the pokie clump?",
            answer=(
                f"{parent.label_word.capitalize()} warned {hero.id} because the pokie clump was prickly and could snag {hero.pronoun('possessive')} {prize.label}. "
                f"It was a cautionary kind of warning, meant to keep the quest safe."
            ),
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help on the quest?",
                answer=(
                    f"{gear.label.capitalize()} covered {hero.pronoun('possessive')} hands, so {hero.id} could fetch the pokie clump without getting scratched."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    out: list[QAItem] = []
    for key in ["pokie", "clump", "quest", "cautionary", "tall tale"]:
        if key in tags or key in KNOWLEDGE:
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="briar_road", quest="quest", prize="bundle", name="Mina", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="hill_lane", quest="quest", prize="bundle", name="Owen", gender="boy", parent="father", trait="curious"),
]


def explain_rejection(quest: Quest, prize: Prize) -> str:
    if not prize_at_risk(quest, prize):
        return "(No story: the prize is not really at risk on this quest.)"
    return "(No story: the quest has no gear fix that truly protects the prize.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("hazard_of", qid, q.hazard))
        for r in sorted(q.zone):
            lines.append(asp.fact("splashes", qid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(Q, P) :- splashes(Q, R), worn_on(P, R).
protects(G, Q, P) :- gear(G), prize_at_risk(Q, P), hazard_of(Q, H), guards(G, H), covers(G, R), worn_on(P, R).
has_fix(Q, P) :- protects(_, Q, P).
valid(Place, Q, P) :- affords(Place, Q), prize_at_risk(Q, P), has_fix(Q, P).
"""


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
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pokie clump quest with cautionary tall-tale style."
    )
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
        quest, prize = QUESTS[args.quest], PRIZES[args.prize]
        if not (prize_at_risk(quest, prize) and select_gear(quest, prize)):
            raise StoryError(explain_rejection(quest, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest_id, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, quest, prize) combos:\n")
        for place, quest, prize in triples:
            print(f"  {place:12} {quest:8} {prize:8}")
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
