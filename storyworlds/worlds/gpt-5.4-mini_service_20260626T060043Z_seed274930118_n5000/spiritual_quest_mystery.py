#!/usr/bin/env python3
"""
storyworlds/worlds/spiritual_quest_mystery.py
=============================================

A small mystery-flavored story world about a spiritual quest: someone follows
clues, asks careful questions, and finds what was missing.

The simulated domain keeps the mystery style close to a gentle children's tale:
a seeker wants to complete a quest, a meaningful object goes missing, small
clues point the way, and the ending reveals what the clues meant.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "nun", "priestess"}
        male = {"boy", "man", "father", "monk", "priest"}
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
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    clue: str
    reveal: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    kind: str
    place: str
    sacred: bool = True
    plural: bool = False


@dataclass
class Charm:
    id: str
    label: str
    guards: set[str]
    clue_fit: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.path: list[str] = []

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
        clone.path = list(self.path)
        clone.paragraphs = [[]]
        return clone


def _r_find_clue(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.facts.get("seeker")
    quest = world.facts.get("quest")
    relic = world.facts.get("relic")
    if not seeker or not quest or not relic:
        return out
    if seeker.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if relic.id in world.fired:
        return out
    if quest.id not in world.path:
        return out
    sig = ("clue", quest.id, relic.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"A small clue was waiting there: {quest.clue}.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if "clue" not in world.fired:
        return out
    seeker = world.facts["seeker"]
    quest = world.facts["quest"]
    relic = world.facts["relic"]
    if seeker.memes.get("faith", 0.0) < THRESHOLD:
        return out
    sig = ("reveal", quest.id, relic.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"The clue led to the truth: {quest.reveal}.")
    return out


CAUSAL_RULES = [_r_find_clue, _r_reveal]


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


def path_has_problem(quest: Quest, relic: Relic) -> bool:
    return quest.keyword in relic.phrase.lower() or relic.place in quest.tags


def select_charm(quest: Quest, relic: Relic) -> Optional[Charm]:
    for charm in CHARMS:
        if quest.keyword in charm.guards and relic.kind in charm.clue_fit:
            return charm
    return None


def predict_success(world: World, seeker: Entity, quest: Quest, relic_id: str) -> bool:
    sim = world.copy()
    sim.get(seeker.id).memes["curiosity"] = 1.0
    sim.get(seeker.id).memes["faith"] = 1.0
    sim.path.append(quest.id)
    return relic_id in sim.entities


PLACE_REGISTRY = {
    "temple": Place(id="temple", label="the temple courtyard", tags={"spiritual", "echo", "stone"}),
    "garden": Place(id="garden", label="the quiet garden", tags={"spiritual", "flowers", "paths"}),
    "chapel": Place(id="chapel", label="the little chapel", tags={"spiritual", "bells", "light"}),
    "shrine": Place(id="shrine", label="the shrine by the stream", tags={"spiritual", "water", "trees"}),
}

QUEST_REGISTRY = {
    "lantern": Quest(
        id="lantern",
        verb="find the lantern",
        gerund="following the lantern's glow",
        clue="a warm glow on the stone path",
        reveal="the lantern had been moved beside the prayer steps",
        risk="the glow could be lost in the dark",
        keyword="light",
        tags={"light", "stone"},
    ),
    "bell": Quest(
        id="bell",
        verb="find the bell",
        gerund="listening for the bell's sound",
        clue="a soft ring behind the old curtain",
        reveal="the bell had fallen into a basket of leaves",
        risk="the sound could be hidden by the wind",
        keyword="sound",
        tags={"sound", "leaves"},
    ),
    "bowl": Quest(
        id="bowl",
        verb="find the bowl",
        gerund="searching for the bowl",
        clue="a tiny trail of rice near the bench",
        reveal="the bowl was tucked under a folded cloth",
        risk="the bowl could be mistaken for an ordinary dish",
        keyword="offering",
        tags={"offering", "cloth"},
    ),
    "prayer_scroll": Quest(
        id="prayer_scroll",
        verb="find the prayer scroll",
        gerund="reading the old writing",
        clue="one corner of paper caught in the door",
        reveal="the scroll had slipped behind the wooden screen",
        risk="the writing could be overlooked",
        keyword="prayer",
        tags={"prayer", "paper"},
    ),
}

RELICS = {
    "lantern": Relic(id="lantern", label="lantern", phrase="a lantern used for evening prayers", kind="light", place="temple"),
    "bell": Relic(id="bell", label="bell", phrase="a small bronze bell", kind="sound", place="chapel"),
    "bowl": Relic(id="bowl", label="offering bowl", phrase="a white offering bowl", kind="offering", place="shrine"),
    "scroll": Relic(id="scroll", label="prayer scroll", phrase="an old prayer scroll", kind="prayer", place="garden"),
}

CHARMS = [
    Charm(id="lamp_oil", label="lamp oil", guards={"light"}, clue_fit={"light"}, prep="carry a little lamp oil", tail="held the light steady"),
    Charm(id="listening_shell", label="a listening shell", guards={"sound"}, clue_fit={"sound"}, prep="hold a listening shell near the ear", tail="helped the bell sound clearer"),
    Charm(id="silk_wrap", label="a silk wrap", guards={"prayer"}, clue_fit={"prayer"}, prep="carry a silk wrap carefully", tail="kept the scroll safe"),
    Charm(id="clean_cloth", label="a clean cloth", guards={"offering"}, clue_fit={"offering"}, prep="bring a clean cloth for the bowl", tail="kept the offering bowl bright"),
]

NAMES_GIRL = ["Mina", "Lina", "Tara", "Asha", "Nina", "Riya"]
NAMES_BOY = ["Tomo", "Eli", "Sami", "Noah", "Ivo", "Ravi"]
KINDS = {"girl", "boy", "monk", "nun"}
TRAITS = ["quiet", "curious", "gentle", "patient", "hopeful"]


@dataclass
class StoryParams:
    place: str
    quest: str
    relic: str
    name: str
    kind: str
    guide: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACE_REGISTRY.items():
        for qid, quest in QUEST_REGISTRY.items():
            for rid, relic in RELICS.items():
                if place.id == relic.place and path_has_problem(quest, relic):
                    out.append((pid, qid, rid))
    return out


def _article(s: str) -> str:
    return "an" if s[:1].lower() in "aeiou" else "a"


def explain_rejection(quest: Quest, relic: Relic) -> str:
    return (
        f"(No story: this quest does not fit that relic well. "
        f"The clue would not honestly point to {relic.label}, so the mystery would be too weak.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle spiritual quest mystery story world.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--quest", choices=QUEST_REGISTRY)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--kind", choices=sorted(KINDS))
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=["elder", "abbot", "caretaker", "friend"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, relic = rng.choice(sorted(combos))
    kind = args.kind or rng.choice(["girl", "boy", "monk", "nun"])
    name = args.name or rng.choice(NAMES_GIRL if kind in {"girl", "nun"} else NAMES_BOY)
    guide = args.guide or rng.choice(["elder", "abbot", "caretaker", "friend"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, relic=relic, name=name, kind=kind, guide=guide, trait=trait)


def tell(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    quest = QUEST_REGISTRY[params.quest]
    relic = RELICS[params.relic]
    world = World(place)
    seeker = world.add(Entity(id=params.name, kind="character", type=params.kind, meters={}, memes={"curiosity": 1.0, "faith": 0.0}))
    guide = world.add(Entity(id="Guide", kind="character", type=params.guide, label=f"the {params.guide}"))
    relic_ent = world.add(Entity(id=relic.id, kind="thing", type=relic.kind, label=relic.label, phrase=relic.phrase, caretaker=guide.id))
    world.facts.update(seeker=seeker, guide=guide, quest=quest, relic=relic_ent, params=params)

    world.say(f"In {place.label}, {params.name} was {params.trait} and still as the morning air.")
    world.say(f"{'He' if params.kind in {'boy', 'monk'} else 'She'} had a spiritual quest: to {quest.verb}.")
    world.say(f"The missing thing was {_article(relic.label)} {relic.label}, and everyone felt the silence around it.")

    world.para()
    world.say(f"{params.name} and {guide.label} walked slowly through {place.label}.")
    world.say(f"{params.name} wanted to {quest.verb}, but first had to listen for clues.")
    world.path.append(quest.id)
    world.say(f"They noticed {quest.risk}.")
    world.say(f"{params.name} looked carefully and asked gentle questions.")

    world.para()
    world.say(f"{params.name} chose {select_charm(quest, relic).label if select_charm(quest, relic) else 'a careful heart'} for the search.")
    if select_charm(quest, relic):
        charm = select_charm(quest, relic)
        world.say(f"They could {charm.prep}, and that made the search feel steadier.")
    seeker.memes["faith"] = 1.0
    propagate(world, narrate=True)
    if relic.id == "scroll":
        world.say(f"At last, {params.name} found {quest.reveal}, and the mystery opened like a door.")
    else:
        world.say(f"At last, {params.name} found {quest.reveal}, and the mystery made sense at last.")
    world.say(f"{params.name} smiled because the quest was complete and the sacred thing was safe again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    q = f["quest"]
    r = f["relic"]
    return [
        f'Write a short mysterious story for a child about a spiritual quest in {PLACE_REGISTRY[p.place].label}.',
        f"Tell a gentle mystery where {p.name} tries to {q.verb} and finds {r.label} after following clues.",
        f'Write a child-friendly quest story that uses the word "{q.keyword}" and ends with a calm reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    q = f["quest"]
    r = f["relic"]
    guide = f["guide"]
    qa = [
        QAItem(
            question=f"What spiritual quest was {p.name} trying to finish in {world.place.label}?",
            answer=f"{p.name} was trying to {q.verb}. It was a quiet spiritual quest, so the search stayed gentle and careful.",
        ),
        QAItem(
            question=f"Who helped {p.name} look for {r.label}?",
            answer=f"{p.name} looked with {guide.label}. The helper stayed calm and helped read the clues.",
        ),
        QAItem(
            question=f"What clue led {p.name} toward the answer?",
            answer=f"The clue was {q.clue}. It matched the missing thing and pointed the search in the right direction.",
        ),
        QAItem(
            question=f"What was the ending reveal in the mystery?",
            answer=f"The ending revealed that {q.reveal}. That is why the quest could end happily.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    q = f["quest"]
    r = f["relic"]
    out = [
        QAItem(question="What is a quest?", answer="A quest is a search for something important or a mission to reach a special goal."),
        QAItem(question="What does spiritual mean?", answer="Spiritual means connected to the spirit, faith, prayer, or deep feeling."),
        QAItem(question="What is a clue?", answer="A clue is a small piece of information that helps someone solve a mystery."),
    ]
    if q.keyword == "light":
        out.append(QAItem(question="Why can light help in the dark?", answer="Light helps people see shapes, paths, and things that are easy to miss in shadows."))
    if r.kind == "sound":
        out.append(QAItem(question="What makes a bell useful in a story?", answer="A bell can be heard from far away, so it can help people notice where something is."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  path={world.path}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="temple", quest="lantern", relic="lantern", name="Mina", kind="girl", guide="elder", trait="curious"),
    StoryParams(place="chapel", quest="bell", relic="bell", name="Tomo", kind="boy", guide="abbot", trait="quiet"),
    StoryParams(place="shrine", quest="bowl", relic="bowl", name="Asha", kind="girl", guide="caretaker", trait="gentle"),
    StoryParams(place="garden", quest="prayer_scroll", relic="scroll", name="Ravi", kind="boy", guide="friend", trait="hopeful"),
]


ASP_RULES = r"""
quest_ok(P,Q,R) :- place(P), quest(Q), relic(R), fits(P,Q,R).
fits(P,Q,R) :- place_tag(P,T), quest_tag(Q,T), relic_at(R,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("place_tag", pid, t))
    for qid, q in QUEST_REGISTRY.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_tag", qid, q.keyword))
        for t in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, t))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_at", rid, r.place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show quest_ok/3."))
    return sorted(set(asp.atoms(model, "quest_ok")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show quest_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible quest combos")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
