#!/usr/bin/env python3
"""
storyworlds/worlds/providence_illegal_ethic_conflict_heartwarming.py
====================================================================

A compact story world about a child, a tempting shortcut, and a kind
heartwarming turn.

Seed tale:
---
A child named Tessa is trying to get home before dinner with a jar of
strawberries from her grandma's garden. On the way, she notices a closed,
fenced shortcut through a little community orchard. It would be faster to
sneak through, but her mom says it would be illegal and against their ethic
to use a path that belongs to someone else. Tessa feels torn and upset.

Then providence appears: the orchard keeper arrives, hears the story, and
opens the gate. He thanks Tessa for waiting, gives her a ripe pear for the
road, and invites them to come back tomorrow when the path is officially
open. Tessa walks home relieved, glad she chose honesty.

World model:
---
- meters track physical state like distance, time pressure, fruit freshness,
  and whether a gate is open
- memes track emotional state like conflict, guilt, relief, trust, and joy
- the story is generated from the evolving state, not from a frozen template

The inline ASP twin mirrors the Python reasonableness gate:
- an illegal shortcut is only story-worthy when there is a closed path
- a heartwarming resolution exists only when a keeper can reopen the path
  and offer a kind alternative
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    outdoor: bool
    has_shortcut: bool = False
    kind: str = "neighborhood"


@dataclass
class Temptation:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    legal_phrase: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class KeeperOffer:
    id: str
    label: str
    prep: str
    tail: str
    opens_gate: bool = True
    gives_treat: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    temptation: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "orchard": Place(name="the community orchard", outdoor=True, has_shortcut=True),
    "park": Place(name="the little park", outdoor=True, has_shortcut=True),
    "courtyard": Place(name="the apartment courtyard", outdoor=True, has_shortcut=True),
}

TEMPTATIONS = {
    "shortcut": Temptation(
        id="shortcut",
        verb="cut through the closed shortcut",
        gerund="cutting through the closed shortcut",
        rush="dash through the fence gap",
        risk="trespassing",
        legal_phrase="it was illegal to go through a closed path",
        zone="gate",
        keyword="providence",
        tags={"providence", "illegal"},
    ),
    "berries": Temptation(
        id="berries",
        verb="pick the unattended berries",
        gerund="picking the unattended berries",
        rush="reach for the low branch",
        risk="taking without asking",
        legal_phrase="it would be wrong to take fruit that did not belong to them",
        zone="branch",
        keyword="ethic",
        tags={"ethic", "illegal"},
    ),
}

PRIZES = {
    "strawberries": Prize(id="strawberries", label="strawberries", phrase="a jar of strawberries", region="hands", plural=True),
    "pear": Prize(id="pear", label="pear", phrase="a ripe pear", region="hands"),
    "cookie": Prize(id="cookie", label="cookie", phrase="a wrapped cookie", region="hands"),
}

OFFERS = {
    "gate": KeeperOffer(
        id="gate",
        label="the gate",
        prep="unlock the gate and open it the proper way",
        tail="unlocked the gate and welcomed them in",
    ),
    "basket": KeeperOffer(
        id="basket",
        label="a basket of fruit",
        prep="offer a basket of fruit for the road",
        tail="handed over a basket of fruit with a smile",
    ),
}

NAMES_GIRL = ["Tessa", "Mina", "Ruby", "Nora", "Lila", "June"]
NAMES_BOY = ["Owen", "Theo", "Caleb", "Milo", "Evan", "Finn"]
TRAITS = ["careful", "soft-hearted", "brave", "thoughtful", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, place in PLACES.items():
        if not place.has_shortcut:
            continue
        for t in TEMPTATIONS:
            for r in PRIZES:
                if reasonableness_gate(place, TEMPTATIONS[t], PRIZES[r]):
                    combos.append((p, t, r))
    return combos


def reasonableness_gate(place: Place, temptation: Temptation, prize: Prize) -> bool:
    return place.has_shortcut and prize.region == "hands" and temptation.id in {"shortcut", "berries"}


def select_offer(temptation: Temptation, prize: Prize) -> Optional[KeeperOffer]:
    if temptation.id == "shortcut":
        return OFFERS["gate"]
    if temptation.id == "berries":
        return OFFERS["basket"]
    return None


def predict_outcome(world: World, hero: Entity, temptation: Temptation, prize: Entity) -> dict:
    sim = world.copy()
    _attempt(sim, sim.get(hero.id), temptation, narrate=False)
    return {
        "conflict": sim.get(hero.id).memes.get("conflict", 0.0) >= THRESHOLD,
        "soiled": sim.get(hero.id).meters.get("mud", 0.0) >= THRESHOLD,
    }


def _attempt(world: World, hero: Entity, temptation: Temptation, narrate: bool = True) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    world.trace_bits.append(temptation.id)
    if narrate:
        world.say(f"{hero.id} wanted to {temptation.verb}, but it felt wrong.")
    if temptation.id == "shortcut":
        hero.meters["risk"] = hero.meters.get("risk", 0.0) + 1
    else:
        hero.meters["risk"] = hero.meters.get("risk", 0.0) + 0.5


def propagate(world: World, narrate: bool = True) -> None:
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not hero:
        return
    if hero.memes.get("conflict", 0.0) >= THRESHOLD and not world.fired:
        world.fired.add(("conflict", hero.id))
        if narrate:
            world.say(f"{hero.id} felt stuck between wanting speed and wanting to do the right thing.")


def tell(place: Place, temptation: Temptation, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    keeper = world.add(Entity(id="Keeper", kind="character", type="man", label="the orchard keeper"))

    world.say(f"{hero.id} was a little {temptation.keyword} thinker who noticed every path and gate.")
    world.say(f"{hero.pronoun().capitalize()} carried {hero.pronoun('possessive')} {prize.label} carefully and wanted to get home before dinner.")
    world.para()
    world.say(f"Near {place.name}, {hero.id} saw a closed shortcut that promised a faster way.")
    world.say(f"{hero.id} wanted to {temptation.verb}, but {parent.label_word if hasattr(parent, 'label_word') else 'the parent'} said, \"No, that would be illegal.\"")
    world.say(f"It would break their ethic to use a path that belonged to someone else.")
    _attempt(world, hero, temptation)
    propagate(world)

    world.para()
    world.say(f"{hero.id} frowned and looked at the fence, wishing the choice were simpler.")
    world.say(f"Then, as if by providence, the keeper arrived with a key jingling in {keeper.pronoun('possessive')} pocket.")
    if temptation.id == "shortcut":
        offer = OFFERS["gate"]
        world.say(f"{keeper.id} heard what happened and said it was okay to wait.")
        world.say(f"{keeper.id} could {offer.prep}, because kindness works best when it is honest.")
        hero.memes["conflict"] = 0.0
        hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        prize.meters["fresh"] = 1.0
        world.say(f"At last, {keeper.id} {offer.tail}, and even the nervous little wait began to feel lucky.")
        world.say(f"{keeper.id} handed {hero.pronoun('object')} a ripe pear for the road.")
        world.say(f"{hero.id} thanked {keeper.id}, and the homeward walk felt lighter than before.")
    else:
        offer = OFFERS["basket"]
        world.say(f"{keeper.id} smiled and said that asking first was the right thing to do.")
        world.say(f"{keeper.id} {offer.tail}, and the smell of fruit made the air feel warm.")
        hero.memes["conflict"] = 0.0
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        world.say(f"{hero.id} got to carry the basket home with a grateful heart.")

    world.facts.update(hero=hero, parent=parent, prize=prize, keeper=keeper, place=place,
                       temptation=temptation, offer=offer, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    temptation = f["temptation"]
    prize = f["prize"]
    return [
        f'Write a heartwarming story for a young child about {hero.id}, a closed path, and a choice guided by providence.',
        f"Tell a gentle story where a {hero.type} feels conflict about {temptation.legal_phrase} while carrying {prize.phrase}.",
        f'Write a simple story that includes the words "providence", "illegal", and "ethic" and ends with kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    keeper = f["keeper"]
    prize = f["prize"]
    temptation = f["temptation"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"What made {hero.id} feel torn near {place.name}?",
            answer=f"{hero.id} felt torn because {temptation.legal_phrase}. {parent.label_word if hasattr(parent, 'label_word') else 'The parent'} reminded {hero.pronoun('object')} that it would be illegal and against their ethic.",
        ),
        QAItem(
            question=f"Why did {hero.id} not go through the shortcut right away?",
            answer=f"{hero.id} did not go through because the shortcut was closed and it would have been wrong to break the rules. {hero.id} chose to wait instead of doing something illegal.",
        ),
        QAItem(
            question=f"How did {keeper.id} help {hero.id} and {prize.label} at the end?",
            answer=f"{keeper.id} opened the gate the proper way and offered a kind treat, so {hero.id} could go home safely with {prize.phrase}. That made the ending feel warm and relieved.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did providence change the conflict for {hero.id}?",
                answer=f"Providence arrived when {keeper.id} showed up with a key and a kind answer. The conflict faded because the path was opened honestly and {hero.id} was not asked to choose between speed and ethics anymore.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["temptation"].tags)
    tags.add("providence")
    out = []
    if "providence" in tags:
        out.append(QAItem(
            question="What does providence mean in a story?",
            answer="Providence means a good and helpful thing happens at just the right time, almost as if a lucky door opens when it is needed most.",
        ))
    if "illegal" in tags:
        out.append(QAItem(
            question="What does illegal mean?",
            answer="Illegal means against the law, so it is not allowed and people should not do it.",
        ))
    if "ethic" in tags:
        out.append(QAItem(
            question="What is an ethic?",
            answer="An ethic is a rule or belief about what is right and kind to do, even when no one is watching.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orchard", temptation="shortcut", prize="strawberries", name="Tessa", gender="girl", parent="mother"),
    StoryParams(place="park", temptation="berries", prize="pear", name="Owen", gender="boy", parent="father"),
]


def explain_rejection(place: Place, temptation: Temptation, prize: Prize) -> str:
    return f"(No story: {temptation.legal_phrase} does not fit with {place.name} and {prize.phrase} in this small world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about providence, illegal choices, and ethic under conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
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
    if args.place and args.temptation and args.prize:
        if not reasonableness_gate(PLACES[args.place], TEMPTATIONS[args.temptation], PRIZES[args.prize]):
            raise StoryError(explain_rejection(PLACES[args.place], TEMPTATIONS[args.temptation], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.temptation is None or c[1] == args.temptation)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, temp, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, temptation=temp, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TEMPTATIONS[params.temptation], PRIZES[params.prize], params.name, params.gender, params.parent)
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
place(P) :- setting(P).
shortcut_place(P) :- place(P), has_shortcut(P).
temptation(T) :- temptation_id(T).
prize(Pz) :- prize_id(Pz).

illegal_choice(P, T, Z) :- shortcut_place(P), temptation_id(T), prize_id(Z),
                           path_closed(P, T), legal_risk(T, Z).

heartwarming(P, T, Z) :- illegal_choice(P, T, Z), keeper_can_help(P, T, Z).
valid_story(P, T, Z) :- heartwarming(P, T, Z).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.has_shortcut:
            lines.append(asp.fact("has_shortcut", pid))
    for tid, t in TEMPTATIONS.items():
        lines.append(asp.fact("temptation_id", tid))
        lines.append(asp.fact("path_closed", "orchard", tid))
        lines.append(asp.fact("legal_risk", tid, "strawberries"))
        lines.append(asp.fact("keeper_can_help", "orchard", tid, "strawberries"))
    for z in PRIZES:
        lines.append(asp.fact("prize_id", z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.temptation} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
