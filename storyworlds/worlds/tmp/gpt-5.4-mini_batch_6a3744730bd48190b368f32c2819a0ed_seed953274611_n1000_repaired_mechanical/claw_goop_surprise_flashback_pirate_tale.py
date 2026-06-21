#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/claw_goop_surprise_flashback_pirate_tale.py
=============================================================================

A small pirate-tale storyworld built from the seed words "claw" and "goop".
It tells one of a few closely related child-friendly adventures: a pirate kid
finds a strange gooey clue, gets surprised by a clever claw-hook, flashes back
to an old map lesson, and ends with a changed treasure scene.

This script is standalone and stdlib-only aside from the shared repo modules:
- storyworlds/results.py
- storyworlds/asp.py (lazy import inside ASP helpers)
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "mate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Venue:
    id: str
    place: str
    dark_spot: str
    sound: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    makes_goop: bool = False
    surprise: bool = False
    flashback: bool = False
    tag: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Threat:
    id: str
    label: str
    cling: str
    mess: str
    spread: int = 1
    goopy: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    power: int
    surprise_text: str
    flashback_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_goop(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["gooped"] < THRESHOLD:
            continue
        sig = ("goop", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("deck").meters["mess"] += 1
        out.append(f"The deck got slick with {world.facts['threat'].label}.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_seen") and not world.facts.get("surprise_narrated"):
        world.facts["surprise_narrated"] = True
        out.append("The hidden claw-hook flashed out from the crate like a tiny surprise.")
    return out


CAUSAL_RULES = [Rule("goop", _r_goop), Rule("surprise", _r_surprise)]


def hazard_at_risk(tool: Artifact, threat: Threat) -> bool:
    return tool.makes_goop and threat.goopy


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.power >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_fixes():
        return combos
    for v in VENUES:
        for a in ARTIFACTS:
            for t in THREATS:
                if hazard_at_risk(ARTIFACTS[a], THREATS[t]):
                    combos.append((v, a, t))
    return combos


def story_event(world: World, hero: Entity, mate: Entity, parent: Entity,
                venue: Venue, artifact: Artifact, threat: Threat, fix: Fix) -> None:
    hero.memes["boldness"] += 1
    mate.memes["caution"] += 1
    world.say(
        f"On a salty afternoon aboard the {venue.place}, {hero.id} and {mate.id} "
        f"were hunting for treasure near {venue.dark_spot}."
    )
    world.say(
        f"The air smelled of tar and sea-salt, and the {venue.sound} of the ship made "
        f"the old boards feel alive."
    )
    world.say(
        f"Then {hero.id} found {artifact.phrase} beside a crate. "
        f"{artifact.label.capitalize()} looked strange, and a little too clever to trust."
    )
    world.say(
        f"Before the others could blink, {mate.id} pointed at the mess. "
        f'"That {threat.label} is going to spread," {mate.id} said. "Call {parent.id}!"'
    )
    world.facts["surprise_seen"] = artifact.surprise
    if artifact.flashback:
        world.para()
        world.say(
            f"{hero.id} remembered an old lesson from the captain: once, a map "
            f"had been ruined by sticky {threat.label}, and the crew had to work twice as hard."
        )
        hero.memes["flashback"] += 1
    if artifact.surprise:
        world.say(
            f"Inside the crate, a little claw-hook snapped open with a bright clack, "
            f"and everyone jumped."
        )
    world.para()
    sim = world.copy()
    sim.get("goop").meters["gooped"] += 1
    propagate(sim, narrate=False)
    world.say(
        f"{parent.id} came running with {fix.label}. {parent.pronoun().capitalize()} "
        f"{fix.surprise_text}."
    )
    world.say(
        f"{parent.pronoun().capitalize()} then remembered the flashback and used it "
        f"the sensible way: {fix.flashback_text}."
    )
    world.say(
        f"The {threat.label} stopped creeping, the deck dried enough to walk on, and "
        f"{venue.ending_image}."
    )
    hero.memes["relief"] += 1
    mate.memes["relief"] += 1
    parent.memes["pride"] += 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the words "{f["artifact"].label}" and "{f["threat"].label}".',
        f"Tell a story where a surprise from a {f['artifact'].label} helps solve a messy {f['threat'].label} problem on a ship.",
        "Write a child-friendly pirate story with a flashback to an older lesson and an ending that proves the mess got handled.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate, parent = f["hero"], f["mate"], f["parent"]
    venue, artifact, threat, fix = f["venue"], f["artifact"], f["threat"], f["fix"]
    return [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {mate.id}, and {parent.id} on a pirate ship. The three of them turn a small mess into a safe adventure.",
        ),
        (
            f"What did {hero.id} find?",
            f"{hero.id} found {artifact.phrase}. It was a surprise, and it led straight to the problem with {threat.label}.",
        ),
        (
            "Why did the story include a flashback?",
            f"The flashback reminded {hero.id} of an older lesson about sticky messes. That memory helped the crew choose a sensible fix instead of panicking.",
        ),
        (
            "How did the problem get solved?",
            f"{parent.id} used {fix.label} to handle the {threat.label}. The fix stopped the goop and left the deck safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["artifact"].tags) | set(world.facts["threat"].tags) | set(world.facts["fix"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    venue: str
    artifact: str
    threat: str
    fix: str
    hero: str
    mate: str
    parent: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


VENUES = {
    "deck": Venue("deck", "deck", "the lantern crate", "creak of ropes", "the lanterns glowed steady again", {"pirate"}),
    "hold": Venue("hold", "cargo hold", "the wet corner", "thump of waves", "the old hold felt calm again", {"pirate"}),
}

ARTIFACTS = {
    "claw": Artifact("claw", "claw-hook", "a brass claw-hook", makes_goop=False, surprise=True, flashback=False, tag="claw", tags={"claw", "surprise"}),
    "map": Artifact("map", "map tube", "an old map tube", makes_goop=False, surprise=True, flashback=True, tag="map", tags={"flashback"}),
    "jar": Artifact("jar", "jar", "a tiny jar with a grin painted on it", makes_goop=True, surprise=True, flashback=True, tag="jar", tags={"claw", "goop", "surprise", "flashback"}),
}

THREATS = {
    "goop": Threat("goop", "goop", "the sticky goop", "goopy"),
    "slime": Threat("slime", "slime", "the green slime", "slimy"),
}

FIXES = {
    "cloth": Fix("cloth", "a dry sail cloth", "a dry sail cloth", 2, "lifted up a dry sail cloth and covered the mess at once", "remembered that a dry cloth worked better than a bare hand", "covered the goop with dry cloth so the deck stayed safe", {"cloth"}),
    "bucket": Fix("bucket", "a bucket of seawater", "a bucket of seawater", 3, "grabbed a bucket of seawater from the rail", "remembered the captain's lesson about quick cleanup", "used seawater and cloth together to stop the spread", {"bucket"}),
}

KNOWLEDGE = {
    "claw": [("What is a claw-hook?", "A claw-hook is a hooked tool that can grab or lift things. On a ship, it can help pull stuff closer without using your hands.")],
    "goop": [("What is goop?", "Goop is a sticky, messy blob that can spread and cling to things. It can make a deck slippery if nobody cleans it up.")],
    "flashback": [("What is a flashback in a story?", "A flashback is a quick memory of something that happened earlier. It helps explain why a character knows what to do now.")],
    "surprise": [("What is a surprise in a story?", "A surprise is something unexpected that makes the characters react right away. It can be funny, exciting, or a little scary.")],
    "pirate": [("What is a pirate ship?", "A pirate ship is a boat in a pretend adventure story, with sails, ropes, and a deck for exploring.")],
    "cloth": [("Why is a dry cloth useful for a mess?", "A dry cloth can soak up spills and keep them from spreading. It is a simple, safe way to clean.")],
}
KNOWLEDGE_ORDER = ["pirate", "surprise", "flashback", "claw", "goop", "cloth"]


CURATED = [
    StoryParams(venue="deck", artifact="jar", threat="goop", fix="cloth", hero="Pip", mate="Miri", parent="Captain Ada"),
    StoryParams(venue="hold", artifact="claw", threat="goop", fix="bucket", hero="Nico", mate="Suri", parent="Captain Bea"),
]


def explain_rejection(artifact: Artifact, threat: Threat) -> str:
    if not hazard_at_risk(artifact, threat):
        return f"(No story: {artifact.label} does not create the right kind of mess for {threat.label}.)"
    return "(No story: this combination cannot make a reasonable pirate-mess story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale world with claw-hooks, goop, surprise, and flashback.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--mate")
    ap.add_argument("--parent")
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
    if args.artifact and args.threat and not hazard_at_risk(ARTIFACTS[args.artifact], THREATS[args.threat]):
        raise StoryError(explain_rejection(ARTIFACTS[args.artifact], THREATS[args.threat]))
    combos = [c for c in valid_combos()
              if (args.venue is None or c[0] == args.venue)
              and (args.artifact is None or c[1] == args.artifact)
              and (args.threat is None or c[2] == args.threat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    venue, artifact, threat = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero = args.hero or rng.choice(["Pip", "Nico", "Suri", "Miri", "Tess"])
    mate = args.mate or rng.choice([n for n in ["Pip", "Nico", "Suri", "Miri", "Tess"] if n != hero])
    parent = args.parent or rng.choice(["Captain Ada", "Captain Bea"])
    return StoryParams(venue=venue, artifact=artifact, threat=threat, fix=fix, hero=hero, mate=mate, parent=parent)


def generate(params: StoryParams) -> StorySample:
    for name in [params.venue, params.artifact, params.threat, params.fix]:
        if name not in globals()[name.upper() + "S" if name != "fix" else "FIXES"]:
            pass
    venue = VENUES.get(params.venue)
    artifact = ARTIFACTS.get(params.artifact)
    threat = THREATS.get(params.threat)
    fix = FIXES.get(params.fix)
    if not (venue and artifact and threat and fix):
        raise StoryError("Invalid params.")
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type="boy", role="hero", tags={"pirate"}))
    mate = world.add(Entity(id=params.mate, kind="character", type="girl", role="mate", tags={"pirate"}))
    parent = world.add(Entity(id=params.parent, kind="character", type="captain", role="parent", tags={"pirate"}))
    deck = world.add(Entity(id="deck", type="place", label="deck"))
    goop = world.add(Entity(id="goop", type="thing", label=threat.label))
    world.facts.update(hero=hero, mate=mate, parent=parent, venue=venue, artifact=artifact, threat=threat, fix=fix)
    story_event(world, hero, mate, parent, venue, artifact, threat, fix)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
hazard(A,T) :- makes_goop(A), goopy(T).
valid(V,A,T) :- venue(V), artifact(A), threat(T), hazard(A,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VENUES:
        lines.append(asp.fact("venue", v))
    for a in ARTIFACTS.values():
        lines.append(asp.fact("artifact", a.id))
        if a.makes_goop:
            lines.append(asp.fact("makes_goop", a.id))
    for t in THREATS.values():
        lines.append(asp.fact("threat", t.id))
        if t.goopy:
            lines.append(asp.fact("goopy", t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between clingo and valid_combos()")
        rc = 1
    else:
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(venue=None, artifact=None, threat=None, fix=None, hero=None, mate=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
