#!/usr/bin/env python3
"""
storyworlds/worlds/record_gerund_foreshadowing_curiosity_fable.py
=================================================================

A small fable-like storyworld about curiosity, foreshadowing, and a careful
recording habit.

Premise:
- A curious animal wants to record a sound, sign, or clue in a notebook.
- A tiny warning or overlooked detail foreshadows a helpful or troublesome turn.
- The hero follows curiosity, gathers a record, and learns a gentle lesson.

This world keeps the simulation small and causal:
- physical meters track carried objects, distances, and visible conditions
- emotional memes track curiosity, worry, patience, and relief
- the story text is driven by state changes, not a frozen paragraph template
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "fox"}
        male = {"boy", "father", "dad", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    sign: str
    outcome: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RecordTool:
    id: str
    label: str
    phrase: str
    kind: str
    protects_from: set[str] = field(default_factory=set)
    helps_with: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    record: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


PLACES = {
    "meadow": Place(id="meadow", label="the meadow", affords={"listen", "follow", "record"}),
    "woods": Place(id="woods", label="the woods", affords={"listen", "follow", "record"}),
    "riverbank": Place(id="riverbank", label="the riverbank", affords={"listen", "follow", "record"}),
    "barnyard": Place(id="barnyard", label="the barnyard", affords={"listen", "record"}),
}

ACTIONS = {
    "birdsong": Action(
        id="birdsong",
        verb="record the birdsong",
        gerund="recording birdsong",
        sign="a small song from the hedges",
        outcome="the note on the page became a clear little song map",
        risk="the tune would be lost if no one listened closely",
        tags={"sound", "bird", "listening"},
    ),
    "footprints": Action(
        id="footprints",
        verb="record the footprints",
        gerund="recording footprints",
        sign="tiny prints beside the path",
        outcome="the marks told a neat story of who had passed by",
        risk="the prints would fade if the ground dried too soon",
        tags={"track", "mud", "path"},
    ),
    "raindrops": Action(
        id="raindrops",
        verb="record the raindrops",
        gerund="recording raindrops",
        sign="a soft tapping on leaves",
        outcome="the page held a little pattern of wet dots and timing",
        risk="the page would smear if the rain came harder",
        tags={"rain", "sound", "weather"},
    ),
}

RECORDS = {
    "notebook": RecordTool(
        id="notebook",
        label="a little notebook",
        phrase="a little notebook with a bright string",
        kind="paper",
        protects_from=set(),
        helps_with={"sound", "track", "weather"},
    ),
    "wax-tablet": RecordTool(
        id="wax-tablet",
        label="a wax tablet",
        phrase="a smooth wax tablet",
        kind="wax",
        protects_from={"rain"},
        helps_with={"track", "sound"},
    ),
    "reed-pen": RecordTool(
        id="reed-pen",
        label="a reed pen",
        phrase="a reed pen and a soft pouch",
        kind="pen",
        protects_from={"mud"},
        helps_with={"sound", "weather"},
    ),
}

GUESSES = [
    "It is wise to look closely before the answer slips away.",
    "A small clue can lead a careful heart to a big truth.",
    "Curiosity is best when it walks with patience.",
    "What is noticed early need not be regretted later.",
]

NAMES = {
    "girl": ["Mina", "Luna", "Tessa", "Nina", "Pippa"],
    "boy": ["Otis", "Robin", "Milo", "Evan", "Jonah"],
}
TRAITS = ["curious", "gentle", "patient", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for action_id, action in ACTIONS.items():
            if "record" not in place.affords:
                continue
            for record_id, record in RECORDS.items():
                if action.id in {"raindrops"} and "rain" not in record.protects_from and record.kind == "paper":
                    continue
                if action.id in {"footprints"} and record.kind == "wax":
                    continue
                if action.id in {"birdsong"} and record.kind == "wax":
                    out.append((place_id, action_id, record_id))
                elif action.id in {"birdsong", "footprints", "raindrops"}:
                    if action.tags & record.helps_with:
                        out.append((place_id, action_id, record_id))
    return sorted(set(out))


def reason_gating(action: Action, record: RecordTool) -> bool:
    if action.id == "raindrops" and record.kind == "paper":
        return False
    if action.id == "footprints" and record.kind == "wax":
        return False
    return bool(action.tags & record.helps_with) or (action.id == "birdsong" and record.kind == "wax")


def explain_rejection(action: Action, record: RecordTool) -> str:
    return (
        f"(No story: {record.label} does not fit {action.gerund} well enough. "
        f"The story needs a real reason the tool helps the curious hero.)"
    )


def explain_gender(record_id: str, gender: str) -> str:
    return f"(No story: this story uses a {record_id}, but the requested {gender} choice does not fit the sampled hero.)"


def tell_opening(world: World, hero: Entity, guide: Entity, action: Action, record: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.memes.get('traits', []) if t != 'little' and t != hero.type) if hero.memes.get('traits') else hero.type} {hero.type} "
        f"who loved to notice small things."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked {action.gerund} because {action.sign} always felt like a clue."
    )
    world.say(
        f"One day, {guide.label} gave {hero.id} {record.phrase}, and {hero.id} treasured it."
    )


def predict_turn(world: World, hero: Entity, action: Action, record: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["curiosity"] += 1
    sim.get(hero.id).meters["distance"] += 1
    if action.id == "raindrops":
        sim.get(record.id).meters["wet"] = 1
    if action.id == "footprints":
        sim.get(record.id).meters["mud"] = 1
    return {
        "foreshadowed": action.risk,
        "record_safe": record.meters.get("wet", 0) < THRESHOLD,
    }


def tell_middle(world: World, hero: Entity, guide: Entity, action: Action, record: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.para()
    world.say(f"Late that morning, {hero.id} went to {world.place.label}.")
    world.say(f"{hero.pronoun().capitalize()} noticed {action.sign}, and that small sign tugged at {hero.pronoun('possessive')} mind.")
    world.say(f"{hero.id} wanted to {action.verb}, but {guide.label} had already warned, \"{action.risk.capitalize()}.\"")

    if action.id == "raindrops":
        record.meters["wet"] = 0
        if record.kind == "paper":
            record.meters["tucked_under_leaf"] = 1
            hero.memes["worry"] += 1
            world.say("The sky darkened, and the first drop made the leaves shiver.")
            world.say(f"{hero.id} quickly tucked {record.it()} under a broad leaf before the rain could smear it.")
        else:
            world.say(f"{hero.id} held {record.it()} under a dry eave, where the drops could still be heard but not damage the page.")
    elif action.id == "footprints":
        record.meters["mud"] = 1
        world.say("The path near the stream looked soft, and one set of prints nearly vanished in the dust.")
        world.say(f"{hero.id} knelt down and pressed {record.it()} close, copying the prints before they faded.")
    else:
        world.say("A bird sang once from the hedges, then fell quiet as if the day were holding its breath.")
        world.say(f"{hero.id} waited without speaking, and {record.label} caught the second song more clearly than the first.")

    if predict_turn(world, hero, action, record)["foreshadowed"]:
        world.say(f"That little warning proved true, and it made {hero.id} more careful.")

    hero.memes["patience"] += 1


def tell_resolution(world: World, hero: Entity, guide: Entity, action: Action, record: Entity) -> None:
    world.para()
    hero.memes["joy"] += 1
    hero.memes["curiosity"] += 1
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1.0)
    world.say(f"In the end, {hero.id}'s careful notes made sense of the whole morning.")
    world.say(action.outcome.capitalize() + ".")
    world.say(
        f"{guide.label} smiled and said, \"{hero.id}, curiosity is a fine lantern when it is carried with care.\""
    )
    world.say(f"{hero.id} went home with {record.label}, and the little record had become a true lesson.")


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    action = ACTIONS[params.action]
    record_def = RECORDS[params.record]
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"distance": 0.0},
        memes={"curiosity": 1.0, "patience": 0.0, "joy": 0.0, "worry": 0.0, "traits": ["little", params.trait, params.gender]},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type="owl",
        label=f"the {params.guide}",
        memes={"calm": 1.0},
    ))
    record = world.add(Entity(
        id=record_def.id,
        type=record_def.kind,
        label=record_def.label,
        phrase=record_def.phrase,
        owner=hero.id,
        caretaker=guide.id,
        carried_by=hero.id,
        meters={"wet": 0.0, "mud": 0.0},
    ))
    world.facts.update(hero=hero, guide=guide, record=record, action=action, place=place, record_def=record_def)

    tell_opening(world, hero, guide, action, record)
    tell_middle(world, hero, guide, action, record)
    tell_resolution(world, hero, guide, action, record)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    place = f["place"]
    record = f["record_def"]
    return [
        f'Write a short fable about a curious {hero.type} named {hero.id} at {place.label} who wants to {action.verb}.',
        f"Tell a gentle story where a small warning matters, and a {record.label} helps {hero.id} remember a clue.",
        f'Write a child-friendly fable using the word "{action.id}" and a lesson about careful curiosity.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    action = f["action"]
    record = f["record_def"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.label}?",
            answer=f"{hero.id} wanted to {action.verb}. {hero.pronoun().capitalize()} paid attention because the small sign looked important.",
        ),
        QAItem(
            question=f"Why did {guide.label} warn {hero.id} about the day?",
            answer=f"{guide.label} warned {hero.id} because {action.risk}. The warning foreshadowed what would happen, so {hero.id} could act in time.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep the clue safe?",
            answer=f"{record.label} helped {hero.id} keep the clue safe, and that made the final record useful instead of ruined.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and calmer at the end, because curiosity led to a good lesson instead of a careless mistake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small hint in a story that gives an early sign about what may happen later.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to learn, look closely, and ask questions about things you do not yet know.",
        ),
        QAItem(
            question="Why can a record be helpful?",
            answer="A record can be helpful because it helps someone remember a sound, a sight, or a clue after the moment has passed.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", action="birdsong", record="wax-tablet", name="Mina", gender="girl", guide="owl", trait="curious"),
    StoryParams(place="woods", action="footprints", record="notebook", name="Robin", gender="boy", guide="owl", trait="thoughtful"),
    StoryParams(place="riverbank", action="raindrops", record="wax-tablet", name="Luna", gender="girl", guide="owl", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld of curiosity and foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--record", choices=RECORDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", default="owl")
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
    if args.action and args.record:
        if not reason_gating(ACTIONS[args.action], RECORDS[args.record]):
            raise StoryError(explain_rejection(ACTIONS[args.action], RECORDS[args.record]))
    if args.gender and args.record and args.gender not in {"girl", "boy"}:
        raise StoryError(explain_gender(args.record, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.action is None or c[1] == args.action)
        and (args.record is None or c[2] == args.record)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, record = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)
    guide = args.guide or "owl"
    return StoryParams(place=place, action=action, record=record, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
place(Place) :- setting(Place).
action(Action) :- action_def(Action).
record(Record) :- record_def(Record).

valid(Place,Action,Record) :- affords(Place,record), action_def(Action), record_def(Record),
                              supports(Record,Action).
valid_story(Place,Action,Record,Gender) :- valid(Place,Action,Record), fits_gender(Gender).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action_def", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for rid, r in RECORDS.items():
        lines.append(asp.fact("record_def", rid))
        lines.append(asp.fact("supports", rid, "birdsong" if rid == "wax-tablet" else "footprints" if rid == "notebook" else "raindrops"))
        if r.protects_from:
            for m in sorted(r.protects_from):
                lines.append(asp.fact("protects_from", rid, m))
    lines.append(asp.fact("fits_gender", "girl"))
    lines.append(asp.fact("fits_gender", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos_asp())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos_asp()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.action} at {p.place} (record: {p.record})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
