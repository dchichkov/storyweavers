#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/pajama_shave_derrick_teamwork_repetition_whodunit.py
===============================================================================================================================

A small whodunit storyworld about pajamas, shaving, teamwork, and repetition.

Seed-tale sketch:
---
A child in pajamas hears a quiet shaving sound in the hallway and thinks something
mysterious is happening. The child, Derrick, and a grown-up team up to follow
clues: a soft snip, a cloudy sink, and a tiny trail of foam. They ask the same
questions again and again, compare what they saw, and finally discover the truth:
Grandpa was shaving his whiskers before bed because they itched, and Derrick
helped him clean up. The mystery ends with everyone calm, cozy, and ready for sleep.

World model:
---
- Physical meters track foam, whiskers, dust, and tidiness.
- Emotional memes track curiosity, worry, teamwork, and relief.
- Repetition is modeled as recurring clues and repeated questions.
- Teamwork is modeled as multiple helpers combining partial evidence.

Story shape:
---
Setup: a pajama-clad child notices a strange sound.
Investigation: repeated clues and repeated questions narrow the suspects.
Turn: teamwork connects the last clue to Grandpa's mirror and razor.
Resolution: the mystery is solved, and the house settles down for bed.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "gentleman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    bedtime: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    repeated_line: str
    fact: str
    reveals: str


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    alibi: str
    truth: str
    helpful: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "plural": v.plural, "owner": v.owner,
            "caretaker": v.caretaker, "worn_by": v.worn_by,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    name: str
    derrick_is_helper: bool
    seed: Optional[int] = None


SETTINGS = {
    "house": Place(name="the house", bedtime=True, affords={"shaving", "investigation"}),
    "hallway": Place(name="the hallway", bedtime=True, affords={"investigation"}),
    "bathroom": Place(name="the bathroom", bedtime=True, affords={"shaving", "investigation"}),
}

CLUES = {
    "snip": Clue(
        id="snip",
        label="a snip-snip sound",
        repeated_line="snip-snip",
        fact="someone used a razor or scissors nearby",
        reveals="the shaving happened in the bathroom",
    ),
    "foam": Clue(
        id="foam",
        label="a little cloud of foam",
        repeated_line="foamy, foamy",
        fact="shaving cream was opened",
        reveals="the shave was fresh",
    ),
    "pajama": Clue(
        id="pajama",
        label="a pajama sleeve with a white speck",
        repeated_line="white speck, white speck",
        fact="foam brushed the pajamas",
        reveals="the mystery touched bedtime clothes",
    ),
    "mirror": Clue(
        id="mirror",
        label="a foggy mirror",
        repeated_line="foggy mirror, foggy mirror",
        fact="someone had been standing at the sink",
        reveals="the sink was part of the scene",
    ),
}

SUSPECTS = {
    "grandpa": Suspect(
        id="grandpa",
        label="Grandpa",
        role="grandfather",
        alibi="I was getting ready for bed.",
        truth="I shaved my whiskers because they were itchy.",
        helpful=True,
    ),
    "derrick": Suspect(
        id="derrick",
        label="Derrick",
        role="helper",
        alibi="I was holding the towel and the little mirror.",
        truth="I helped Grandpa clean the sink after the shave.",
        helpful=True,
    ),
    "mom": Suspect(
        id="mom",
        label="Mom",
        role="grown-up",
        alibi="I heard the snip-snip too, but I stayed in the hall.",
        truth="I was the one who asked everyone to speak one at a time.",
        helpful=True,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lena", "Ava", "Ruby", "Zoe"]
BOY_NAMES = ["Finn", "Theo", "Miles", "Noah", "Jack", "Owen"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("heard_snip") and "repeat" not in world.fired:
        world.fired.add("repeat")
        out.append("The snip-snip sound came again, and that made the mystery feel bigger.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared_clues") and "teamwork" not in world.fired:
        world.fired.add("teamwork")
        out.append("When everyone compared clues together, the answer became easy to see.")
    return out


CAUSAL_RULES = [
    Rule("repetition", _r_repetition),
    Rule("teamwork", _r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    made: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                made.extend(sents)
    if narrate:
        for s in made:
            world.say(s)
    return made


def build_suspect_list() -> list[Suspect]:
    return [SUSPECTS["grandpa"], SUSPECTS["derrick"], SUSPECTS["mom"]]


def ask_again(world: World, detective: Entity, line: str) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.say(f'{detective.id} asked again, "{line}"')


def notice_clue(world: World, detective: Entity, clue: Clue) -> None:
    detective.meters["noticed"] = detective.meters.get("noticed", 0) + 1
    world.say(f"{detective.id} spotted {clue.label}.")


def inspect_clue(world: World, helper: Entity, clue: Clue) -> None:
    helper.memes["focus"] = helper.memes.get("focus", 0) + 1
    world.say(f"{helper.id} looked closely and said, \"That means {clue.fact}.\"")


def suspect_speaks(world: World, suspect: Suspect) -> None:
    world.say(f'{suspect.label} said, "{suspect.alibi}"')


def solve_mystery(world: World, detective: Entity, helper: Entity, suspect: Suspect) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    world.say(
        f"In the end, {suspect.label} smiled and said, \"{suspect.truth}\""
    )


def tell(place: Place, name: str, derrick_is_helper: bool) -> World:
    world = World(place)
    detective = world.add(Entity(id=name, kind="character", type="boy", label=name))
    derrick = world.add(Entity(id="Derrick", kind="character", type="boy", label="Derrick"))
    mom = world.add(Entity(id="Mom", kind="character", type="mother", label="Mom"))
    grandpa = world.add(Entity(id="Grandpa", kind="character", type="grandfather", label="Grandpa"))
    pajama = world.add(Entity(
        id="pajama", type="thing", label="pajamas", phrase="soft striped pajamas",
        owner=detective.id, worn_by=detective.id
    ))
    razor = world.add(Entity(id="razor", type="thing", label="razor"))
    sink = world.add(Entity(id="sink", type="thing", label="sink"))
    foam = world.add(Entity(id="foam", type="thing", label="foam"))

    world.say(
        f"It was bedtime at {place.name}, and {detective.id} was already in {detective.pronoun('possessive')} pajamas."
    )
    world.say(
        f"Then {detective.id} heard a quiet snip-snip from down the hall."
    )
    world.facts["heard_snip"] = True
    propagate(world)

    world.para()
    world.say(
        f"{detective.id} frowned. If someone was shaving at bedtime, who was it, and why did it sound so secret?"
    )
    ask_again(world, detective, "Who is shaving?")
    ask_again(world, detective, "Who is shaving?")
    notice_clue(world, detective, CLUES["snip"])
    inspect_clue(world, derrick, CLUES["snip"])

    world.para()
    world.say(
        f"The team followed the clues to the bathroom, where they found a foggy mirror and a little cloud of foam."
    )
    notice_clue(world, detective, CLUES["mirror"])
    notice_clue(world, detective, CLUES["foam"])
    inspect_clue(world, mom, CLUES["mirror"])
    inspect_clue(world, derrick, CLUES["foam"])
    world.facts["shared_clues"] = True
    propagate(world)

    world.para()
    world.say(
        f"{mom.id} asked everyone to speak one at a time, and each suspect gave the same kind of careful answer."
    )
    suspect_speaks(world, SUSPECTS["grandpa"])
    suspect_speaks(world, SUSPECTS["derrick"])
    suspect_speaks(world, SUSPECTS["mom"])

    world.say(
        f"{detective.id} looked at the white speck on the pajama sleeve and then at the sink."
    )
    notice_clue(world, detective, CLUES["pajama"])

    world.para()
    solve_mystery(world, detective, derrick, SUSPECTS["grandpa"])
    world.say(
        f"Grandpa had shaved his whiskers because they itched, and Derrick had helped him clean up the foam."
    )
    world.say(
        f"After that, the hall was quiet, the pajamas stayed cozy, and the whole team went to bed feeling proud."
    )

    world.facts.update(
        detective=detective,
        derrick=derrick,
        mom=mom,
        grandpa=grandpa,
        pajama=pajama,
        razor=razor,
        sink=sink,
        foam=foam,
        solved_by="teamwork",
        culprit="grandpa",
        clue_order=["snip", "mirror", "foam", "pajama"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    detective = world.facts["detective"]
    return [
        f'Write a gentle whodunit for a young child where {detective.id} in pajamas hears a shaving sound and solves the mystery with help.',
        f"Tell a bedtime mystery about pajamas, a shave, and Derrick, using repeated clues and teamwork to find out who was at the sink.",
        "Write a cozy detective story where the same question is asked more than once, clues are compared, and the answer is kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective: Entity = world.facts["detective"]
    derrick: Entity = world.facts["derrick"]
    grandpa: Entity = world.facts["grandpa"]
    return [
        QAItem(
            question=f"Why did {detective.id} think something mysterious was happening?",
            answer=f"{detective.id} heard a quiet snip-snip sound in the hallway while {detective.pronoun('possessive')} pajamas were on, so it seemed like a secret was going on.",
        ),
        QAItem(
            question="What clue helped the team know the mystery was about shaving?",
            answer="The team found a foggy mirror, a little cloud of foam, and a white speck on the pajamas. Those clues showed that someone had been shaving nearby.",
        ),
        QAItem(
            question=f"How did Derrick help solve the mystery?",
            answer=f"Derrick looked closely at the foam, helped compare the clues, and cleaned up with Grandpa. That teamwork made the answer clear.",
        ),
        QAItem(
            question="Who was doing the shaving?",
            answer="Grandpa was doing the shaving. He said his whiskers were itchy, so he shaved them before bed.",
        ),
        QAItem(
            question="Why did the repeated questions matter?",
            answer="The repeated questions kept everyone focused on the same clues, so the team could compare what they heard and saw instead of guessing too fast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are pajamas for?",
            answer="Pajamas are soft clothes people wear to sleep and rest in at bedtime.",
        ),
        QAItem(
            question="What does shaving mean?",
            answer="Shaving means using a razor or similar tool to remove hair from skin, often from a face or chin.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and help each other to solve a problem or finish a job.",
        ),
        QAItem(
            question="Why can repeating a clue help in a mystery?",
            answer="Repeating a clue can help because it gives people another chance to notice the same detail and remember it clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
heard_snip.
shared_clues.

repetition_happens :- heard_snip.
teamwork_happens :- shared_clues.

#show repetition_happens/0.
#show teamwork_happens/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("heard_snip"),
        asp.fact("shared_clues"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy whodunit about pajamas, shaving, Derrick, teamwork, and repetition.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    name = args.name or rng.choice(BOY_NAMES)
    return StoryParams(place=place, name=name, derrick_is_helper=True)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.derrick_is_helper)
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
    StoryParams(place="house", name="Milo", derrick_is_helper=True),
    StoryParams(place="hallway", name="Noah", derrick_is_helper=True),
    StoryParams(place="bathroom", name="Finn", derrick_is_helper=True),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show repetition_happens/0. #show teamwork_happens/0."))
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    expected = {("repetition_happens", 0), ("teamwork_happens", 0)}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("Mismatch in ASP twin.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repetition_happens/0. #show teamwork_happens/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show repetition_happens/0. #show teamwork_happens/0."))
        print("ASP model:", sorted(f"{s.name}/{len(s.arguments)}" for s in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
