#!/usr/bin/env python3
"""
storyworlds/worlds/progeny_exhaust_word_dim_sound_effects_pirate.py
===================================================================

A standalone storyworld for a tiny pirate-tale domain with sound effects,
where a captain's progeny, a word-dim clue, and a wearying exhaust problem
shape the ending.

Seed premise:
- A young pirate's progeny wants to play loudly on the deck.
- A word-dim signal or chant matters because a treasure clue glows or fades.
- The ship's exhaust from a little galley stove can tire the crew / smoke the hold.
- Sound effects should make the tale feel like a pirate story, not an event log.

The world is intentionally small:
- People: captain, progeny.
- Places: ship deck, hold, cove, island.
- Things: lantern, map, drum, windlass.
- A simple choice of what to do causes tension and a clear ending image.

Contract notes:
- imports storyworlds/results eagerly and storyworlds/asp lazily
- provides StoryParams, build_parser, resolve_params, generate, emit, main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
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
    role: str = ""
    owner: str = ""
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "daughter"}
        male = {"boy", "father", "dad", "man", "son"}
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
    place_type: str
    sound: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    sound: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    sound: str
    clears: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "deck"
    problem: str = "swell"
    fix: str = "whisper"
    name: str = "Mira"
    gender: str = "girl"
    captain: str = "mother"
    trait: str = "brave"
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    problem: Problem
    fix: Fix
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


PLACES = {
    "deck": Place("deck", "the ship deck", "deck", "clap-clap of boots", allows={"swell", "whistle", "rope"}, tags={"deck"}),
    "hold": Place("hold", "the dark hold", "hold", "creak-creak of boards", allows={"whisper", "glow", "rope"}, tags={"hold"}),
    "cove": Place("cove", "the shell cove", "cove", "splash-splash at the shore", allows={"swell", "whisper", "glow"}, tags={"cove"}),
    "island": Place("island", "the little island", "island", "whoosh of palms", allows={"swell", "whisper"}, tags={"island"}),
}

PROBLEMS = {
    "swell": Problem("swell", "a big sea swell", "watch the swell", "whoooosh!", "rock the lantern loose", tags={"sea", "swell"}),
    "whistle": Problem("whistle", "the wind whistle", "follow the whistle", "fweee!", "shake the map corner", tags={"wind", "whistle"}),
    "rope": Problem("rope", "a tangled rope", "untangle the rope", "snick-snack!", "catch the lantern hook", tags={"rope", "tangle"}),
}

FIXES = {
    "whisper": Fix("whisper", "a whisper plan", "lower their voices and whisper", "shhh!", clears={"whistle"}, tags={"whisper", "word-dim"}),
    "cover": Fix("cover", "a canvas cover", "cover the glowing map with canvas", "flap!", clears={"glow"}, tags={"cover", "canvas"}),
    "drum": Fix("drum", "the drum pack", "play the drum softly to keep time", "boom-boom!", clears={"swell"}, tags={"drum", "sound"}),
}


class StoryWorld:
    def __init__(self, place: Place, problem: Problem, fix: Fix) -> None:
        self.place = place
        self.problem = problem
        self.fix = fix
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for prob in PROBLEMS.values():
            for fx in FIXES.values():
                if prob.id in place.allows and fx.id in {"whisper", "cover", "drum"}:
                    out.append((pid, prob.id, fx.id))
    return out


def explain_rejection(place: Place, problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: {problem.label} and {fix.label} do not make a strong enough pirate tale "
        f"for {place.label}. Pick one of the valid combinations.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["brave", "curious", "restless", "clever"])
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
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mira", "Nina", "Pip", "Nate", "Luna", "Ollie"])
    captain = args.captain or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(["brave", "curious", "restless", "clever"])
    return StoryParams(place=place, problem=problem, fix=fix, name=name, gender=gender, captain=captain, trait=trait)


def _make_world(params: StoryParams) -> StoryWorld:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    world = StoryWorld(place, problem, fix)

    hero = world.add(Entity(id="hero", kind="character", type=params.gender, role="progeny", label=params.name, meters={"mess": 0.0}, memes={"joy": 0.0, "worry": 0.0, "relief": 0.0}))
    captain = world.add(Entity(id="captain", kind="character", type=params.captain, role="captain", label=f"the {params.captain}", meters={"work": 0.0}, memes={"worry": 0.0, "pride": 0.0}))
    lantern = world.add(Entity(id="lantern", kind="thing", type="thing", label="lantern", phrase="a brass lantern", owner=hero.id, place=place.id, meters={"dim": 0.0}, memes={"glow": 0.0}, tags={"glow"}))
    mapent = world.add(Entity(id="map", kind="thing", type="thing", label="map", phrase="a word-dim treasure map", owner=hero.id, place=place.id, meters={"dim": 0.0}, memes={"secrecy": 0.0}, tags={"word-dim"}))
    windlass = world.add(Entity(id="windlass", kind="thing", type="thing", label="windlass", phrase="a ship windlass", place=place.id, meters={"exhaust": 0.0}, memes={"strain": 0.0}, tags={"exhaust"}))

    world.facts = {
        "hero": hero,
        "captain": captain,
        "lantern": lantern,
        "map": mapent,
        "windlass": windlass,
        "place": place,
        "problem": problem,
        "fix": fix,
        "risk": problem.risk,
        "word_dim": True,
    }

    return world


def _propagate(world: StoryWorld) -> None:
    hero = world.facts["hero"]
    lantern = world.facts["lantern"]
    mapent = world.facts["map"]
    windlass = world.facts["windlass"]
    problem = world.facts["problem"]

    sig = ("exhaust", problem.id)
    if sig not in world.fired and windlass.meters["exhaust"] >= THRESHOLD:
        world.fired.add(sig)
        hero.memes["worry"] += 1
        lantern.meters["dim"] += 1
        world.say("The lantern went dim-dim, and the little deck felt gloomier.")

    sig2 = ("word_dim", problem.id)
    if sig2 not in world.fired and mapent.meters["dim"] >= THRESHOLD:
        world.fired.add(sig2)
        mapent.memes["secrecy"] += 1
        world.say("The word-dim map grew faint, like a secret hiding under moonlight.")


def tell(params: StoryParams) -> StoryWorld:
    world = _make_world(params)
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    lantern = world.facts["lantern"]
    mapent = world.facts["map"]
    windlass = world.facts["windlass"]
    place = world.facts["place"]
    problem = world.facts["problem"]
    fix = world.facts["fix"]

    hero.memes["joy"] += 1
    world.say(f"On the {place.label}, {hero.label} was the captain's progeny, quick-footed and full of bounce.")
    world.say(f'"Clap-clap! {problem.sound}" went the {place.sound}, and {hero.label} grinned at the singing air.')
    world.say(f"{hero.label} loved the {mapent.phrase}, especially the word-dim clue that shimmered with pirate mystery.")

    world.para()
    captain.memes["worry"] += 1
    world.say(f"But {problem.label} made the {lantern.label} sway, and the little ship felt tired enough to exhaust the crew.")
    world.say(f'"{fix.sound}" said the plan, because the {fix.label} could keep the clue safe without a fuss.')

    if params.fix == "drum":
        windlass.meters["exhaust"] += 1
        hero.memes["joy"] += 1
        world.say(f"{hero.label} tapped the drum softly: boom-boom, boom-boom, until the deck settled.")
    elif params.fix == "cover":
        mapent.meters["dim"] += 1
        world.say(f"{hero.label} covered the map: flap! The word-dim clue stayed hidden from the bright spray.")
    else:
        world.say(f"{hero.label} whispered low, shhh, and the pirate words dimmed down to a secret hush.")

    _propagate(world)

    world.para()
    captain.memes["pride"] += 1
    hero.memes["relief"] += 1
    world.say(f"In the end, {hero.label} stood by the railing with {place.label} wind in {hero.pronoun('possessive')} hair.")
    if params.fix == "cover":
        world.say(f"The map was folded safe and neat, no longer word-dim and lost in the glare.")
    elif params.fix == "whisper":
        world.say(f"The clue stayed clear because the whisper kept the word-dim secret from fluttering away.")
    else:
        world.say(f"The drumbeat had eased the crew, and even the exhaust from the little windlass seemed to sleep.")
    world.facts.update(resolved=True, ending=hero.memes["relief"] >= THRESHOLD)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    hero = world.facts["hero"]
    place = world.facts["place"]
    problem = world.facts["problem"]
    fix = world.facts["fix"]
    return [
        f'Write a short pirate tale for a child named {hero.label} on {place.label} with the word "progeny".',
        f"Tell a pirate story where {hero.label} worries about {problem.label} and uses {fix.label} to keep the clue safe.",
        'Write a child-friendly pirate scene that includes sound effects, the word "word-dim", and a gentle ending.',
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    place = world.facts["place"]
    problem = world.facts["problem"]
    fix = world.facts["fix"]
    mapent = world.facts["map"]
    lantern = world.facts["lantern"]
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.label} is on {place.label} with the captain?",
            answer=f"It is about {hero.label}, the captain's progeny, and the grown-up pirate who watches over {hero.pronoun('possessive')} adventure. They are out on {place.label}, where the sea sounds keep changing.",
        ),
        QAItem(
            question=f"Why did the lantern start to feel dim on {place.label}?",
            answer=f"The problem was {problem.label}, which made the ship feel more worn and made the lantern sway. That is why the light could not stay bright without help.",
        ),
        QAItem(
            question=f"What did {hero.label} do with the {fix.label} plan?",
            answer=f"{hero.label} used {fix.phrase} to solve the trouble in a safe pirate way. The plan helped the word-dim clue stay useful instead of fading away.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(QAItem(
            question=f"What proved that the ending changed on {place.label}?",
            answer=f"The lantern stayed steady, and the map stayed clear enough to read. That final image shows the crew had found a calmer way to keep exploring.",
        ))
    return qa


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does progeny mean?",
            answer="Progeny means a child or children. In a pirate tale, it can point to the captain's son or daughter.",
        ),
        QAItem(
            question="What does exhaust mean?",
            answer="Exhaust can mean to make someone very tired. It can also mean the gases or smoke that come out of a machine or engine.",
        ),
        QAItem(
            question="What does word-dim mean here?",
            answer="Word-dim means words or clues that are fading, faint, or hard to see. A whispered plan can keep a word-dim clue from disappearing.",
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


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.place:
            bits.append(f"place={ent.place}")
        lines.append(f"  {ent.id:8} ({ent.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="deck", problem="swell", fix="drum", name="Mira", gender="girl", captain="mother", trait="brave"),
    StoryParams(place="hold", problem="whistle", fix="whisper", name="Pip", gender="boy", captain="father", trait="curious"),
    StoryParams(place="cove", problem="rope", fix="cover", name="Luna", gender="girl", captain="mother", trait="clever"),
    StoryParams(place="island", problem="swell", fix="whisper", name="Ollie", gender="boy", captain="father", trait="restless"),
]


ASP_RULES = r"""
valid(P, Pr, F) :- place(P), problem(Pr), fix(F), allowed(P, Pr), fix_ok(F, Pr).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for a in sorted(p.allows):
            lines.append(asp.fact("allowed", p.id, a))
    for pr in PROBLEMS.values():
        lines.append(asp.fact("problem", pr.id))
    for fx in FIXES.values():
        lines.append(asp.fact("fix", fx.id))
        for c in sorted(fx.clears):
            lines.append(asp.fact("fix_ok", fx.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH between clingo and valid_combos().")
        print("only in python:", sorted(py - cl))
        print("only in clingo:", sorted(cl - py))
    sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, fix=None, name=None, gender=None, captain=None, trait=None), random.Random(777)))
    assert sample.story
    print("OK: smoke-tested story generation.")
    return ok


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    if (params.place, params.problem, params.fix) not in valid_combos():
        raise StoryError(explain_rejection(PLACES[params.place], PROBLEMS[params.problem], FIXES[params.fix]))
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
    if trace and sample.world:
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
        for row in asp_valid_combos():
            print(row)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(50, args.n * 50)):
            if len(samples) >= args.n:
                break
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            if p.story if False else False:
                pass
            sample = generate(p)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
