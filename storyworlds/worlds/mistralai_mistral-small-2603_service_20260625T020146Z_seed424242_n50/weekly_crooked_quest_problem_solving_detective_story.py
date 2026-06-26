#!/usr/bin/env python3
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 0.8

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    parent: Optional[str] = None
    region: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"detective", "assistant", "client"}
        male = {"suspect"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them"

    @property
    def title(self) -> str:
        return {"detective": "Detective", "client": "Client", "suspect": "Suspect"}.get(self.type, self.type)

class World:
    def __init__(self, case_number: int, setting: str = "office") -> None:
        self.case_number = case_number
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.case_number, self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_collect_evidence(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        if "evidence" not in actor.meters:
            continue
        sig = ("collect", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["evidence"] += 1
        out.append(f"{actor.title} {actor.pronoun('object')}'s eyes lit up with a promising clue!")
    return out

def _r_build_case(world: World) -> list[str]:
    detective = next((e for e in world.entities.values() if e.type == "detective"), None)
    if not detective:
        return []
    if detective.memes["confidence"] < THRESHOLD:
        return []
    sig = ("build_case",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    return ["A solid case was beginning to take shape in Detective's mind."]

CAUSAL_RULES: list[Rule] = [
    Rule(name="evidence", tag="clue", apply=_r_collect_evidence),
    Rule(name="build_case", tag="deduction", apply=_r_build_case),
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
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def introduce_detective(world: World) -> None:
    world.add(Entity(
        id="Detective", kind="character", type="detective",
        label="the lead detective", phrase="the clever detective",
        meters={"evidence": 0, "confidence": 0.2, "curiosity": 1.0}
    ))

def hire_assistant(world: World) -> None:
    world.add(Entity(
        id="Assistant", kind="character", type="assistant",
        label="the detective's assistant", phrase="the helpful assistant",
        meters={"clues_processed": 0}, parent="Detective"
    ))

def meet_client(world: World, name: str = "Mrs. Baker") -> None:
    client = world.add(Entity(
        id="Client", kind="character", type="client",
        label=name.lower(), phrase=f"a worried woman in a blue coat named {name}",
        meters={"stress": 0.8}, memes={"distress": 1.0}
    ))
    world.say(
        f"Detective sat quietly as {client.label} described the "
        f"weekly {world.setting} problem."
    )
    client.memes["distress"] -= 0.3
    return client

def describe_problem(world: World, twist: str = "missing gold") -> None:
    world.say(
        f"The case involved a {'weekly' if random.random() > 0.5 else 'regular'} "
        f"delivery of {"weekly vegetables" if random.random() > 0.3 else "office supplies"} "
        f"that had vanished."
    )
    world.say(f"Something about this theft felt particularly {'crooked' if random.random() > 0.5 else 'suspicious'}.")

def identify_suspect(world: World, name: str = "Reginald") -> Entity:
    suspect = world.add(Entity(
        id="Suspect", kind="character", type="suspect",
        label=name.lower(), phrase=f"a quiet man named {name} who works odd shifts",
        meters={"suspicion": 0}, memes={"shadiness": 0.7}
    ))
    world.say(
        f"Detective's sharp eyes noticed {suspect.label} had "
        f"{"crooked handwriting" if random.random() > 0.5 else "a nervous twitch"} "
        f"when the topic came up."
    )
    suspect.memes["shadiness"] += 0.4
    return suspect

def examine_venue(world: World, location: str = "warehouse") -> None:
    world.para()
    world.say(
        f"The {"weekly produce delivery" if "vegetable" in world.setting else "office supplies"} "
        f"was supposed to arrive {"Monday morning" if random.random() > 0.5 else "Tuesday afternoon"} "
        f"at the {location}."
    )
    world.say(
        "The security camera footage showed a figure slipping "
        f"{"away with a bag" if random.random() > 0.5 else "in and out too quickly"}."
    )

def question_witnesses(world: World) -> None:
    world.para()
    world.say("Detective carefully questioned nearby workers.")
    world.add(Entity(
        id="Witness1", kind="character", type="witness", label="cashier",
        phrase="the store cashier who saw everything",
        memes={"honesty": 0.2}
    ))
    world.say("\"I saw someone in a brown jacket,\" the cashier mentioned quietly.")
    world.add(Entity(
        id="Witness2", kind="character", type="witness", label="cleaner",
        phrase="the night cleaner who noticed strange footsteps",
        memes={"observant": 0.9}
    ))
    world.say("\"I swept the floor at 3 AM,\" mentioned the cleaner. \"The prints led to the back door.\"")

def notice_clues(world: World) -> None:
    world.para()
    world.say("The detective spotted small details others missed.")

    Entity(id="ClueBag", kind="thing", type="evidence", label="bag", phrase="a crumpled brown paper bag")
    Entity(id="CluePrints", kind="thing", type="evidence", label="footprints", phrase="muddy footprints")
    Entity(id="ClueReceipt", kind="thing", type="evidence", label="receipt", phrase="a torn receipt with Friday's date")

    for clue in [world.entities["ClueBag"], world.entities["CluePrints"], world.entities["ClueReceipt"]]:
        clue.owner = "Detective"
        world.entities[clue.id].meters["relevance"] = 0.9

def track_path(world: World) -> None:
    world.para()
    world.say(
        "Following the trail, detective discovered the footprints led to a "
        f"{"nearby alley" if random.random() > 0.5 else "storage closet"} where "
        f"the {"gold" if "gold" in world.setting else "supplies"} had been hidden."
    )
    world.say("A torn receipt on the floor confirmed the theft.")

def reveal_truth(world: World, suspect: Entity, client: Entity) -> None:
    world.para()
    if suspect.memes["shadiness"] > 0.8:
        world.say(
            f"Confronted with the mounting evidence, {client.label} confessed "
            f"that {suspect.label} had {"weekly" if random.random() > 0.5 else ""} "
            f"taken the {"gold" if "gold" in world.setting else "supplies"} to sell at "
            f"the {"weekly flea market" if random.random() > 0.5 else "pawn shop"}."
        )
    else:
        world.say(
            f"After piecing together the clues, {suspect.label} admitted "
            f"to taking the {"weekly items" if "weekly" in world.setting else "goods"} "
            f"because {"weekly" if random.random() > 0.5 else "the"} pay had been cut."
        )
    world.say(
        "Detective secured the return of the missing items and "
        f"{"closed the case successfully" if suspect.memes["shadiness"] > 0.8 else "helped resolve the misunderstanding"}."
    )
    detective = world.get("Detective")
    detective.memes["confidence"] = 1.0

def solve_case(setting: str, client_name: str = "Mrs. Baker", suspect_name: str = "Reginald", case_num: int = 42, week_type: str = "regular") -> World:
    world = World(case_num, setting)

    introduce_detective(world)
    hire_assistant(world)

    world.para()
    client = meet_client(world, client_name)

    world.para()
    describe_problem(world, twist="their weekly delivery missing")

    world.para()
    suspect = identify_suspect(world, suspect_name)
    examine_venue(world, setting)

    world.para()
    question_witnesses(world)

    world.para()
    notice_clues(world)

    world.para()
    track_path(world)

    world.para()
    reveal_truth(world, suspect, client)

    detective = world.get("Detective")
    assistant = world.get("Assistant")

    world.facts.update(
        client=client, suspect=suspect,
        detectives=[detective, assistant],
        case_number=case_num,
        setting=setting,
        solution=("crooked" if suspect.memes["shadiness"] > 0.8 else "misunderstanding")
    )
    return world

@dataclass
class StoryParams:
    case_number: int
    setting: str
    client_name: str
    suspect_name: str
    week_type: str
    seed: Optional[int] = None

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    client, suspect, case_num = f["client"], f["suspect"], f["case_number"]
    week_part = "weekly" if f["week_type"] == "weekly" else "mysterious"
    crook_part = "crooked situation" if suspect.memes["shadiness"] > 0.8 else "odd mystery"
    return [
        f'Write a <500-word detective story for ages 6-8 about a clever detective '
        f'solving a {week_part} {crook_part}. Include the names "{client.id}" and '
        f'"{suspect.id}".',
        "Compose a short narrative where a problem is discovered, clues are collected, "
        f"and a truth is uncovered in a {world.setting}. Make the language concrete "
        "and keep dialogue minimal.",
        f'Craft a 3-paragraph mystery featuring a detective using evidence to solve '
        f'a case involving {"weekly produce deliveries" if "vegetable" in world.setting else "office supplies"}. '
        f'The story should end with a clear solution and explain how the detective figured it out.'
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    client, suspect, case_num = f["client"], f["suspect"], f["case_number"]
    detective = world.get("Detective")
    return [
        QAItem(
            question=f"Who hired the detective to solve case #{case_num}?",
            answer=f"{detective.title} was hired by {client.label}, a concerned local."
        ),
        QAItem(
            question=f"What specific detail first made Detective suspicious of {suspect.label}?",
            answer=(
                f"Detective noticed {suspect.label} had {"crooked handwriting" if suspect.memes["shadiness"] > 0.8 else "a nervous habit"} "
                f"when the topic came up, and {"worked odd shifts" if suspect.memes["shadiness"] > 0.8 else "was seen near the scene"}."
            )
        ),
        QAItem(
            question=f"How did Detective prove {suspect.label} took the missing items?",
            answer=(
                f"Following {"muddy footprints" if "Prints" in world.entities else "a torn receipt"} "
                f"led Detective to the hidden goods, confirming {suspect.label}'s involvement."
            )
        )
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does a detective do?", answer="A detective solves mysteries by carefully collecting clues and putting together evidence to find out what really happened."),
        QAItem(question="Why look for footprints?", answer="Footprints can show who was at a place and what direction they were going, helping detectives follow a trail."),
        QAItem(question="What makes a good clue?", answer="A good clue is something small but important that helps connect the crime to a person or explains what happened.")
    ]

SETTINGS = {"office": "office supplies", "garden": "weekly vegetables", "warehouse": "office supplies"}
CLIENTS = ["Mrs. Baker", "Mr. Cohen", "Ms. Rivera", "Dr. Patel"]
SUSPECTS = ["Reginald", "Maurice", "Doris", "Victor"]
WEEK_TYPES = ["regular", "weekly"]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Weekly crooked quest detective story generator")
    ap.add_argument("--case", type=int, default=None, help="case number")
    ap.add_argument("--setting", choices=SETTINGS, default=None)
    ap.add_argument("--client", choices=CLIENTS, default=None)
    ap.add_argument("--suspect", choices=SUSPECTS, default=None)
    ap.add_argument("--week-type", choices=WEEK_TYPES, default=None)
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
    if args.case is not None and args.case <= 0:
        raise StoryError("(Case number must be positive.)")

    combos = [(s, c, wt) for s in SETTINGS for c in CLIENTS for wt in WEEK_TYPES]
    place, client, week_type = rng.choice(combos)

    return StoryParams(
        case_number=args.case or rng.randint(1, 50),
        setting=place,
        client_name=client,
        suspect_name=rng.choice(SUSPECTS),
        week_type=week_type
    )

def generate(params: StoryParams) -> StorySample:
    world = solve_case(
        params.setting, params.client_name,
        params.suspect_name, params.case_number, params.week_type
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world
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

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: f"{v:.1f}" for k, v in e.meters.items() if v > 0.1}
        memes = {k: f"{v:.1f}" for k, v in e.memes.items() if v > 0.1}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  rules fired: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== World Knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)

ASP_RULES = """
% A case is solved when detective has enough evidence
solved(C) :- case(C), difficulty(D), evidence(C,E), E >= D.

% Enough evidence means solving the case
evidence_required(C,D) :- case(C), difficulty(D).

% Suspect is crooked if their shadiness is high enough
crooked(S) :- suspect(S), shadiness(S,V), V >= 0.7.

% Detective confidence increases with solved cases
confident(D) :- detective(D), cases_solved(C), C >= 3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = [
        asp.fact("case", 1), asp.fact("difficulty", 1, 2),
        asp.fact("case", 2), asp.fact("difficulty", 2, 3),
        asp.fact("case", 3), asp.fact("difficulty", 3, 4),
    ]

    for setting, items in SETTINGS.items():
        main_item = next(iter(items.split()))
        lines.append(asp.fact("setting", setting, main_item))

    for client in CLIENTS:
        lines.append(asp.fact("client", client.lower().replace(" ", "_")))

    for suspect in SUSPECTS:
        lines.append(asp.fact("suspect", suspect.lower()))

    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_solve_case(case_num: int) -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(f":- case({case_num}), not solved({case_num})."))
    return sorted(set(asp.atoms(model, "solved"))) if model else []

def asp_verify() -> int:
    import asp
    for c in [1, 2, 3, 4, 5]:
        res = asp_solve_case(c)
        print(f"Case #{c} solution: {'solved' if res else 'not solved'}")
    return 0

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for c in range(1, 6):
            sol = asp_solve_case(c)
            print(f"Case #{c}: {'🕵️‍♂️ SOLVED' if sol else '📋 OPEN'}")
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []

    if args.all:
        for i in range(15):
            seed = rng.randint(1, 10000)
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            samples.append(generate(p))
    else:
        seen = set()
        for i in range(max(args.n * 3, 50)):
            seed = args.seed + i if args.seed else rng.randint(1, 10000)
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e, file=sys.stderr)
                return
            p.seed = seed
            sample = generate(p)
            text = sample.story
            if text not in seen:
                seen.add(text)
                samples.append(sample)
                if len(samples) == args.n:
                    break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all or len(samples) > 1:
            p = sample.params
            header = (
                f"### Weekly Case #{p.case_number}: Detective Story at "
                f"{p.setting} ({'weekly' if p.week_type == 'weekly' else 'regular'} delivery)"
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
