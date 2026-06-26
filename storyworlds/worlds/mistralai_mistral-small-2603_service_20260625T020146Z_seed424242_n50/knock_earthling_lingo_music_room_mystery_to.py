#!/usr/bin/env python3

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
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

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
    meter: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "nurse", "sister"}
        male = {"boy", "father", "dad", "alien", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "earthling":
            return "they"
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "earthling": "kid"}.get(self.type, self.type)

class World:
    def __init__(self, instrument: str) -> None:
        self.instrument = instrument
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.current_knocks: list[str] = []
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
        clone = World(self.instrument)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.current_knocks = list(self.current_knocks)
        clone.paragraphs = [[]]
        return clone

def _r_hear_knocks(world: World) -> list[str]:
    earthling = next((e for e in world.characters() if "earthling" in e.type), None)
    if not earthling or earthling.meters["confusion"] < THRESHOLD:
        return []
    sig = ("knocks_heard", len(world.current_knocks))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    return [f"{earthling.id} heard another knock coming from the {world.instrument}."]

def _r_recognize_pattern(world: World) -> list[str]:
    earthling = next((e for e in world.characters() if "earthling" in e.type), None)
    if not earthling or earthling.meters["curiosity"] < THRESHOLD:
        return []
    sig = "pattern_recognized"
    if sig in world.fired:
        return []
    world.fired.add(sig)
    return [f"{earthling.id} noticed a funny rhythm: ‘ta-ta-TAA ta-ta-TAA’ — it felt like a secret knock-language!"]

CAUSAL_RULES = [
    Rule(name="knocks_heard", tag="physical", apply=_r_hear_knocks),
    Rule(name="pattern_recognized", tag="social", apply=_r_recognize_pattern),
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
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _do_knock(world: World, who: Entity, key: str) -> None:
    world.current_knocks.append(key)
    earthling = next((e for e in world.characters() if "earthling" in e.type), None)
    if earthling:
        earthling.meters["confusion"] += 0.4
        earthling.memes["curiosity"] += 0.2
    propagate(world)

def introduce_music_room(world: World, earthling_name: str = "Liam") -> None:
    earthling = world.add(Entity(
        id=earthling_name,
        kind="character",
        type="earthling",
        label="a curious earthling",
        phrase=f"a curious earthling named {earthling_name}",
        traits=["playful", "stubborn"],
    ))
    piano = world.add(Entity(
        id="piano",
        kind="thing",
        type="piano",
        label="the piano",
        phrase="a shiny grand piano with keys that gleam in the spotlight",
        region="keys",
        plural=False,
    ))
    world.say(f"{earthling.id} wandered into the music room and stared at {piano.label}.")

def starts_practicing(world: World, earthling_name: str) -> None:
    earthling = world.get(earthling_name)
    earthling.memes["joy"] += 1
    world.say(f"{earthling.id} flopped onto the piano bench and started to noodle around on {earthling.pronoun('possessive')} favorite tune — ‘Twinkle Twinkle Little Star’.")

def first_knock(world: World, earthling_name: str) -> None:
    earthling = world.get(earthling_name)
    world.para()
    planet = {"boy": "Mars", "girl": "Saturn", "alien": "Alpha Centauri"}.get(earthling.type, "Earth")
    world.say(f"Just as {earthling.id} played the opening notes, a single sharp knock came from {earthling.pronoun('possessive')} {world.instrument} — a single ‘C’ played with surprising force!")
    _do_knock(world, None, "C")
    world.say(f"‘Huh?’ {earthling.id.capitalize()} giggled. ‘That sounded almost like… a hello from another planet — maybe {planet}?’")

def second_knock(world: World, earthling_name: str) -> None:
    world.say("A pause. Then another, softer knock — ‘E’ this time — seemed to tap along with the melody.")
    _do_knock(world, None, "E")
    world.say("The notes made the keys shimmer for half a second.")

def third_knock(world: World, earthling_name: str) -> None:
    world.say("Another knock — a bold ‘G’ — rang out right on the beat. Now {earthling_name}'s eyebrows lifted.").format(earthling_name=earthling_name)
    _do_knock(world, None, "G")
    world.say("‘You’re copying me!’ {earthling_name} whispered.").format(earthling_name=earthling_name)

def investigate(world: World, earthling_name: str) -> None:
    earthling = world.get(earthling_name)
    world.para()
    world.say(f"{earthling.id} leaned over and played a little three-note run — C-E-G — and listened hard.")
    world.say("Sure enough, the same three knocks answered back: C-E-G, C-E-G, over and over.")
    earthling.memes["curiosity"] += 0.8
    earthling.meters["confusion"] -= 0.3
    propagate(world)

def offer_a_tune(world: World, earthling_name: str, alien_name: str = "Zog") -> None:
    earthling = world.get(earthling_name)
    world.para()
    world.say(f'"Hey, {alien_name}!" {earthling.id} called toward the shadowy corner. "Want to play a duet?"')
    alien = world.add(Entity(
        id=alien_name,
        kind="character",
        type="alien",
        label=alien_name,
        phrase=f"a tiny green alien named {alien_name} with big curious eyes",
        traits=["playful", "polite"],
    ))
    alien.memes["amusement"] += 0.5
    world.say(f"{alien.id} peeped out from behind {earthling.pronoun('possessive')} music stand, holding a tiny controller that looked like a toy xylophone.")

def mystery_resolved(world: World) -> None:
    world.para()
    world.say("Together they launched into a bouncy, giggly rendition of ‘Row, Row, Row Your Boat’ that shook the sheet music rack but lifted the sound right out the open window where any passers-by could have sworn they heard celestial laughter.")
    for e in world.characters():
        e.memes["joy"] += 1
    world.facts["moral_value"] = "communication"

INSTRUMENTS = {
    "piano": {"label": "a grand piano", "plural": False, "article": "a"},
    "violin": {"label": "a shiny violin", "plural": False, "article": "a"},
    "xylophone": {"label": "a colorful xylophone", "plural": False, "article": "a"},
    "drums": {"label": "a snare drum", "plural": False, "article": "a"},
}

EARTHLING_NAMES = ["Liam", "Mia", "Noah", "Emma", "Ethan"]
ALIEN_NAMES = ["Zog", "Fizz", "Blip", "Gleep", "Zara"]
MORAL_VALUES = ["communication", "patience", "understanding"]

@dataclass
class StoryParams:
    instrument: str
    earthling_name: str
    alien_name: str
    seed: Optional[int] = None

def valid_combos():
    for inst in INSTRUMENTS:
        for earthling in EARTHLING_NAMES[:2]:
            for alien in ALIEN_NAMES[:3]:
                yield (inst, earthling, alien)

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = next((e for e in world.characters() if "earthling" in e.type), None)
    alien = next((e for e in world.characters() if "alien" in e.type), None)
    inst = world.instrument
    kw = inst
    return [
        f'Write a silly joke-style story for 4-to-7-year-olds about a kid in a music room who hears mysterious knocks on {inst}.',
        f"A 3-paragraph comedy skit where {hero.id} thinks the {inst} is haunted by ghosts until a friendly alien named {alien.id} pops out and they turn knocking into a duet.",
        f'Make a short, funny tale that includes the word "knock" and explains how listening carefully can solve a mystery.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = next((e for e in world.characters() if "earthling" in e.type), None)
    alien = next((e for e in world.characters() if "alien" in e.type), None)
    moral = f.get("moral_value", "communication")
    para1 = world.paragraphs[0][0] if world.paragraphs[0] else ""
    para2 = world.paragraphs[1][0] if len(world.paragraphs) > 1 else ""
    para3 = world.paragraphs[2][0] if len(world.paragraphs) > 2 else ""
    qa = [
        QAItem(
            question="Who first noticed the mysterious knocks coming from the instrument?",
            answer=f"{hero.id} was the one who flopped onto {hero.pronoun('possessive')} {INSTRUMENTS[world.instrument]['label']} and immediately heard it."
        ),
        QAItem(
            question="What funny rhythm did the knocking copy?",
            answer="The knocks played the notes ‘C-E-G’ over and over, copying the tune the kid was trying to play."
        ),
        QAItem(
            question="What did the earthling and the alien do after solving the mystery?",
            answer=f"Together they played a bouncy duet of ‘Row, Row, Row Your Boat’ and everyone laughed."
        ),
    ]
    if moral == "communication":
        qa.append(QAItem(
            question="What is one lesson the story wants kids to learn?",
            answer="Taking time to listen carefully helps you understand other people — or aliens!"
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    qa = []
    if "piano" in world.instrument or world.instrument == "piano":
        qa.append(QAItem(
            question="Why do piano keys make sounds?",
            answer="Inside a piano there are tiny hammers that hit wires when you press the keys. The wires vibrate and make the musical notes."
        ))
    qa.append(QAItem(
        question="What is knock spelled backwards?",
        answer="Backwards it spells K-N-O-W, showing that listening leads to knowing!"
    ))
    return qa

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- Simulated World State ---"]
    for e in world.entities.values():
        meters = {k: f"{v:.1f}" for k, v in e.meters.items() if v}
        memes = {k: f"{v:.1f}" for k, v in e.memes.items() if v}
        attrs = []
        if meters: attrs.append(f"meters={meters}")
        if memes: attrs.append(f"memes={memes}")
        if attrs:
            lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(attrs)}")
    lines.append(f"  fired rules: {sorted(set(n for n,*_ in world.fired))}")
    lines.append(f"  knock sequence: {', '.join(world.current_knocks) if world.current_knocks else 'none'}")
    return "\n".join(lines)

ASP_RULES = r"""
% Valid instruments for the music room
instrument(piano).
instrument(violin).
instrument(xylophone).
instrument(drums).

% Valid names and moral values
name(earthling,E) :- name_kind(E,"earthling").
name(alien,A) :- name_kind(A,"alien").
moral(M) :- moral_value(M).

% A story is valid if the chosen instrument, earthling name, and alien name match
valid(Inst, En, An, M) :- instrument(Inst), name(earthling,En), name(alien,An), moral(M).

% Backstop: always accept the base program (needed when --asp is run without constraints)
:- not valid(_,_,_,_).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for inst in INSTRUMENTS:
        lines.append(asp.fact("instrument", inst))
    for n in EARTHLING_NAMES[:4]:
        lines.append(asp.fact("name_kind", n, "earthling"))
    for n in ALIEN_NAMES[:5]:
        lines.append(asp.fact("name_kind", n, "alien"))
    lines.append(asp.fact("moral_value", "communication"))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import storyworlds.asp as asp
    clingo_models = asp.one_model(asp_program("#show valid/4."))
    clingo_set = set(asp.atoms(clingo_models, "valid"))
    python_set = set((i, e, a, "communication") for (i, e, a) in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python (≈{len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python sets:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy music-room knock mystery")
    ap.add_argument("--instrument", choices=list(INSTRUMENTS), default="piano")
    ap.add_argument("--earthling-name", choices=EARTHLING_NAMES, default=None)
    ap.add_argument("--alien-name", choices=ALIEN_NAMES, default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="curated set")
    ap.add_argument("--trace", action="store_true", help="dump model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos via ASP")
    ap.add_argument("--verify", action="store_true", help="ASP/Python parity check")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.all:
        triples = list(valid_combos())
        trio = rng.choice(sorted(triples))
        return StoryParams(instrument=trio[0], earthling_name=trio[1], alien_name=trio[2])
    inst = args.instrument
    earthling = args.earthling_name or rng.choice(EARTHLING_NAMES)
    alien = args.alien_name or rng.choice(ALIEN_NAMES)
    return StoryParams(instrument=inst, earthling_name=earthling, alien_name=alien)

def generate(params: StoryParams) -> StorySample:
    world = World(instrument=params.instrument)
    introduce_music_room(world, params.earthling_name)
    starts_practicing(world, params.earthling_name)
    first_knock(world, params.earthling_name)
    second_knock(world, params.earthling_name)
    third_knock(world, params.earthling_name)
    investigate(world, params.earthling_name)
    offer_a_tune(world, params.earthling_name, params.alien_name)
    mystery_resolved(world)
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
        print("\n" + format_qa(sample))

CURATED = [
    StoryParams(instrument="piano", earthling_name="Liam", alien_name="Zog"),
    StoryParams(instrument="violin", earthling_name="Mia", alien_name="Blip"),
    StoryParams(instrument="xylophone", earthling_name="Noah", alien_name="Fizz"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        models = asp.one_model(asp_program("#show valid/4."))
        atoms = asp.atoms(models, "valid")
        print(f"≈{len(atoms)} valid (instrument, earthling, alien) combos via ASP:")
        for a,b,c,_ in atoms:
            print(f"  {a:12} {b:12} {c:12}")
        return
    base_seed = args.seed or random.randrange(2**31)
    samples: list[StorySample] = []
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
        header = "" if len(samples) == 1 else f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
