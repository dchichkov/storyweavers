#!/usr/bin/env python3
"""A gentle bedtime tale where a child learns to share through a small, quiet act.

Build the emotional physics first: reluctance creates distance, and generosity
builds connection. Start with a familiar setting (bedtime) and introduce a
foreshadowing detail (a warm, comforting object). The tension arises from the
child's desire to keep the comfort for themselves. The turn is the decision to
share, which resolves the social tension and provides a safe ending image.

The domain focuses on "nose" as the physical anchor (blowing snot into the nose
is messy/private; sharing breath/whispers is intimate). We model the "mess" of
keeping to oneself versus the "clean" warmth of sharing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Callable, Optional

# The example must run directly as well as through the exporter.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities: characters and objects.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "object"
    type: str = "thing"            # boy, girl, bear, blanket, nose ...
    label: str = ""                # short reference
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    # Physical meter: state of comfort or mess
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    # Emotional meme: feelings like hesitation, warmth, shyness
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


# ---------------------------------------------------------------------------
# World Model
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[Event] = []
        self.facts: dict = {}
        self.turn = 0

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def record(self, kind: str, text: str, *, cause: str = "", result: str = "") -> None:
        self.history.append(Event(kind=kind, actor="", target="", text=text,
                                  cause=cause, result=result))
        self.say(text)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: replace(v) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.turn = self.turn
        return clone


# ---------------------------------------------------------------------------
# Causal Rules
# ---------------------------------------------------------------------------
@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


def _r_sharing_glow(world: World) -> list[str]:
    """If hero shares comfort, warmth spreads to parent."""
    out = []
    hero = world.get(world.facts["hero"].id)
    parent = world.get(world.facts["parent"].id)
    if hero.meters["shared"] >= 1 and parent.memes["warmth"] < 1:
        sig = ("glow", world.turn)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        parent.memes["warmth"] += 1
        hero.memes["joy"] += 1
        out.append("A tiny glow seemed to come from the space between their noses.")
    return out


def _r_healing(world: World) -> list[str]:
    """When the nose is cleaned and shared, the feeling of isolation fades."""
    out = []
    hero = world.get(world.facts["hero"].id)
    if hero.memes["shyness"] > 0 and hero.meters["shared"] >= 1:
        sig = ("heal", world.turn)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["shyness"] = 0
        hero.memes["peace"] += 1
        out.append(f"{hero.pronoun().capitalize()} felt light again, like a bubble floating up.")
    return out


CAUSAL_RULES = [
    _r_sharing_glow,
    _r_healing,
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                world.say(sents[0])


# ---------------------------------------------------------------------------
# Content Registries
# ---------------------------------------------------------------------------
HERO_NAMES_GIRL = ["Lily", "Mia", "Zoe", "Ava"]
HERO_NAMES_BOY = ["Tim", "Ben", "Max", "Sam"]

OBJECTS = {
    "bear": Entity(id="bear", type="toy", label="stuffed bear", phrase="soft brown stuffed bear"),
    "blanket": Entity(id="blanket", type="cloth", label="flannel blanket", phrase="crinkly blue flannel blanket"),
}

SETTINGS = {
    "bedroom": "the quiet bedroom",
    "couch": "the living room couch",
}

PROBLEMS = {
    "sniffle": "A tickle in the nose made {name} snuffle a little.",
    "shy": "{name} felt a bit shy about being so close.",
}

TURNS = {
    "share_breath": "share a warm breath",
    "lean_in": "lean in close",
}

ENDINGS = {
    "sleep": "drifted off to sleep",
    "smile": "smiled softly",
}


# ---------------------------------------------------------------------------
# Story Generation Logic
# ---------------------------------------------------------------------------
def tell_story(params: "StoryParams") -> World:
    world = World()
    setting_text = SETTINGS[params.setting]
    
    # Create entities
    gender_type = params.gender
    name = params.name
    hero = world.add(Entity(id=name, kind="character", type=gender_type, label=name))
    parent = world.add(Entity(id="Parent", kind="character", type="adult", label="Parent"))
    obj = world.add(replace(OBJECTS[params.object], owner=hero.id))
    
    world.facts.update(hero=hero, parent=parent, obj=obj, setting=setting_text,
                       problem=params.problem, turn=params.turn)
    
    # Initial State
    hero.memes["comfort"] = 1
    if params.problem == "sniffle":
        hero.meters["messy_nose"] = 1
        hero.memes["discomfort"] = 1
    else:
        hero.memes["shyness"] = 1

    # 1. Beginning: Setting the scene & Foreshadowing
    openers = {
        "sniffle": f"The room was soft and dim. {name} sat beside {parent.label}, holding {obj.phrase}. A faint itch prickled near {hero.pronoun('possessive')} nose, a secret tingling that wanted attention.",
        "shy": f"The moonlight painted the floor in silver. {name} wrapped {hero.pronoun('possessive')} arms around {obj.phrase}, feeling the steady weight of it against {hero.pronoun('possessive')} chest."
    }
    world.record("start", openers[params.problem])
    
    # 2. Tension: The Problem
    problems = {
        "sniffle": PROBLEMS["sniffle"],
        "shy": PROBLEMS["shy"],
    }
    prob_text = problems[params.problem].format(name=name)
    
    # Foreshadowing beat: The object hints at sharing
    foreshadow = {
        "bear": f"{obj.label.capitalize()}’s fuzzy face seemed to look toward {parent.label}, inviting closeness.",
        "blanket": f"The corner of the {obj.label} drifted over {parent.label}'s knee, waiting to be pulled closer."
    }[params.object]
    
    world.para()
    world.record("tension", f"{prob_text} {foreshadow}")
    hero.memes["hesitation"] += 1

    # 3. Turn: The Decision to Share
    turns = {
        "share_breath": TURNS["share_breath"],
        "lean_in": TURNS["lean_in"],
    }
    action_text = {
        "share_breath": f'{name} took a deep breath in through {hero.pronoun('possessive')} nose, then gently exhaled the warm air toward {parent.label}.',
        "lean_in": f'{name} pushed {obj.label} slightly away and leaned {hero.pronoun()} head closer to {parent.label}',
    }[params.turn]
    
    world.para()
    world.record("turn", action_text)
    hero.meters["shared"] = 1
    propagate(world)

    # 4. Resolution: The Result
    endings = {
        "sleep": ENDINGS["sleep"],
        "smile": ENDINGS["smile"],
    }
    end_text = endings[params.ending]
    
    closing = {
        "sleep": f'Eyes heavy, {name} {end_text}, {obj.label} tucked securely in {hero.pronoun('possessive')} lap.',
        "smile": f'A quiet understanding passed between them, and {name} {end_text}, no longer alone.',
    }[params.ending]
    
    world.para()
    world.record("end", closing)
    hero.memes["peace"] = 1
    
    return world


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    gender: str
    object: str
    setting: str
    problem: str
    turn: str
    ending: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A Generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["obj"]
    kw = "sharing" if f["turn"] == "share_breath" else "closeness"
    return [
        f'Write a gentle bedtime story about {hero.id} who learns to {kw} using {obj.label}.',
        f"Tell a quiet tale where {hero.id} overcomes hesitation by sharing a moment of comfort with a parent."
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "start": "What were they doing at the beginning?",
        "tension": "Why did the character feel uncertain?",
        "turn": "What brave thing did the character do?",
        "end": "How did the story end?"
    }
    out = []
    for e in world.history:
        if e.kind in questions:
            ans_parts = [e.cause, e.result] if e.cause else [e.text]
            # Ensure answer is full sentence and natural
            base_ans = e.text
            if e.cause and e.result:
                 base_ans = f"{e.cause} This led to {e.result.lower()}"
            out.append(QAItem(question=questions[e.kind], answer=base_ans))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    # Generic knowledge about the concepts
    return [
        QAItem(question="What does it mean to share feelings?", 
               answer="Sharing feelings means letting someone else know how you feel, like when you hug someone or talk about something happy or sad."),
        QAItem(question="Why is breathing important in this story?", 
               answer="In this story, breathing represents a quiet way to connect. Exhaling gently shows trust and care without needing many words."),
    ]


# ---------------------------------------------------------------------------
# Validation / Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple]:
    names = GIRL_NAMES + BOY_NAMES
    objs = list(OBJECTS.keys())
    settings = list(SETTINGS.keys())
    problems = list(PROBLEMS.keys())
    turns = list(TURNS.keys())
    endings = list(ENDINGS.keys())
    combos = []
    for n in names:
        g = "girl" if n in GIRL_NAMES else "boy"
        for o in objs:
            for s in settings:
                for p in problems:
                    for t in turns:
                        for e in endings:
                            combos.append((n, g, o, s, p, t, e))
    return combos


ASP_RULES = r"""
% Valid stories require a known character, object, setting, problem, turn, and ending.
valid_story(Name, Gender, Object, Setting, Problem, Turn, Ending) :-
    name(Name, Gender),
    object(Object),
    setting(Setting),
    problem(Problem),
    turn(Turn),
    ending(Ending).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for n in GIRL_NAMES:
        lines.append(asp.fact("name", n, "girl"))
    for n in BOY_NAMES:
        lines.append(asp.fact("name", n, "boy"))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for t in TURNS:
        lines.append(asp.fact("turn", t))
    for e in ENDINGS:
        lines.append(asp.fact("ending", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world.facts["resolved"] if "resolved" in world.facts else True
    assert len(world.paragraphs) >= 4
    assert "nose" in sample.story.lower() or "breath" in sample.story.lower()
    # Check no internal ids leak
    assert not any(marker in sample.story for marker in ("{", "}", "__", "meters=", "memes="))


def asp_verify() -> int:
    import asp
    expected = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/7."))
    asp_set = set(asp.atoms(model, "valid_story"))
    if expected != asp_set:
        print("MISMATCH")
        return 1
    # Check a few generated stories
    checked = 0
    for combo in sorted(expected)[:5]:
        n, g, o, s, p, t, e = combo
        params = StoryParams(name=n, gender=g, object=o, setting=s, problem=p, turn=t, ending=e)
        try:
            sample = generate(params)
            check_sample(sample)
            checked += 1
        except StoryError:
            pass
    print(f"OK: {len(expected)} ASP combos, {checked} story checks.")
    return 0


# ---------------------------------------------------------------------------
# Standard Interface
# ---------------------------------------------------------------------------
GIRL_NAMES = HERO_NAMES_GIRL
BOY_NAMES = HERO_NAMES_BOY

CURATED = [
    StoryParams(name="Lily", gender="girl", object="bear", setting="bedroom", problem="sniffle", turn="share_breath", ending="sleep"),
    StoryParams(name="Ben", gender="boy", object="blanket", setting="couch", problem="shy", turn="lean_in", ending="smile"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime sharing story generator.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--object", choices=list(OBJECTS.keys()))
    ap.add_argument("--setting", choices=list(SETTINGS.keys()))
    ap.add_argument("--problem", choices=list(PROBLEMS.keys()))
    ap.add_argument("--turn", choices=list(TURNS.keys()))
    ap.add_argument("--ending", choices=list(ENDINGS.keys()))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    names = [n for n in GIRL_NAMES + BOY_NAMES if args.name is None or n == args.name]
    if args.gender:
        names = [n for n in names if (n in GIRL_NAMES and args.gender == "girl") or (n in BOY_NAMES and args.gender == "boy")]
    if not names:
        raise StoryError("No matching names found.")
    
    name = rng.choice(names)
    gender = "girl" if name in GIRL_NAMES else "boy"
    
    objects = [o for o in OBJECTS if args.object is None or o == args.object]
    settings = [s for s in SETTINGS if args.setting is None or s == args.setting]
    problems = [p for p in PROBLEMS if args.problem is None or p == args.problem]
    turns = [t for t in TURNS if args.turn is None or t == args.turn]
    endings = [e for e in ENDINGS if args.ending is None or e == args.ending]
    
    if not all([objects, settings, problems, turns, endings]):
        raise StoryError("Invalid combination of constraints.")
        
    return StoryParams(
        name=name,
        gender=gender,
        object=rng.choice(objects),
        setting=rng.choice(settings),
        problem=rng.choice(problems),
        turn=rng.choice(turns),
        ending=rng.choice(endings)
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    if qa:
        print("\n== Prompts ==")
        for p in sample.prompts: print(p)
        print("\n== Story Q&A ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== World Q&A ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def main():
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/7."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/7."))
        atoms = asp.atoms(model, "valid_story")
        print(f"{len(atoms)} valid stories.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < 100:
            try:
                p = resolve_params(args, random.Random(base_seed + i))
                p.seed = base_seed + i
                s = generate(p)
                if s.story not in seen:
                    seen.add(s.story)
                    samples.append(s)
            except StoryError:
                pass
            i += 1
    
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2))
    else:
        for i, s in enumerate(samples):
            emit(s, header=f"### Story {i+1}" if len(samples)>1 else "")
            if i < len(samples)-1: print("---")

if __name__ == "__main__":
    main()
