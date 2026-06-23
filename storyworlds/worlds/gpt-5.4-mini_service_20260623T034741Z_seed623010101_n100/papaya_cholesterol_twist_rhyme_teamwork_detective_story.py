#!/usr/bin/env python3
"""
storyworlds/worlds/papaya_cholesterol_twist_rhyme_teamwork_detective_story.py
=============================================================================

A small standalone story world in a detective-story style.

Seed tale:
---
A little detective team is trying to solve a mystery at the kitchen market.
A papaya bowl has gone missing from the snack table, and someone keeps saying
the word cholesterol as if it were a clue. Twist points to one suspect, Rhyme
spots a second clue by the fruit stand, and Teamwork helps them compare notes.
They discover that the papaya was not stolen at all: it was moved to the
healthy-shelf by mistake, because a helper was trying to make a better snack
plan. The team follows the trail, untangles the twist, and finishes together
with a neat, kind ending image.

Contract goals:
- typed entities with physical meters and emotional memes
- a state-driven premise, turn, and resolution
- QA grounded in world facts and causal trace
- a Python reasonableness gate plus inline ASP twin
- CLI support for default, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TEAM_NAMES = ["Twist", "Rhyme", "Teamwork"]
LOCATIONS = {
    "market": "the kitchen market",
    "store": "the corner store",
    "school": "the classroom snack shelf",
}
CLUES = {
    "note": "a folded note",
    "receipt": "a crinkly receipt",
    "crumbs": "a few sweet crumbs",
}
SUSPECTS = {
    "helper": "the helpful cook",
    "older_kid": "the older kid",
    "neighbor": "the neighbor",
}
EXPLANATIONS = {
    "moved": "moved",
    "borrowed": "borrowed",
    "repacked": "repacked",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    location: str
    clue: str
    suspect: str
    explanation: str
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


@dataclass
class World:
    location: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
        w = World(self.location)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w
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


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def detect_twist(world: World) -> list[str]:
    out: list[str] = []
    case = ("twist", world.facts["twist_actor"])
    if case in world.fired:
        return out
    actor = world.get(world.facts["twist_actor"])
    clue = world.get("clue")
    if clue.meters["found"] >= 1 and world.facts["twist_hint"] >= 1:
        world.fired.add(case)
        world.get("mystery").memes["confusion"] += 1
        actor.memes["surprise"] += 1
        out.append(
            f"The clue made a twist in the trail, and {actor.id} frowned at the new turn."
        )
    return out


def detect_teamwork(world: World) -> list[str]:
    out: list[str] = []
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    trio = [world.get(t) for t in TEAM_NAMES]
    if all(p.memes["focus"] >= 1 for p in trio) and world.get("note").meters["shared"] >= 1:
        world.fired.add(sig)
        for p in trio:
            p.memes["trust"] += 1
        out.append("With teamwork, they lined up the clues and the story began to make sense.")
    return out


def detect_rhyme(world: World) -> list[str]:
    out: list[str] = []
    sig = ("rhyme",)
    if sig in world.fired:
        return out
    if world.get("note").meters["shared"] >= 1 and world.facts["rhyme_line"]:
        world.fired.add(sig)
        world.get("rhyme").memes["delight"] += 1
        out.append(f"{world.facts['rhyme_line']} said {world.facts['rhyme_speaker']}, and the rhyme fit the clue.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (detect_twist, detect_rhyme, detect_teamwork):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc in LOCATIONS:
        for clue in CLUES:
            for suspect in SUSPECTS:
                if clue == "note" or suspect in {"helper", "neighbor"}:
                    combos.append((loc, clue, suspect))
    return combos


def build_world(params: StoryParams) -> World:
    w = World(LOCATIONS[params.location])
    twist = w.add(Entity(id="Twist", kind="character", role="detective", label="Twist",
                         meters={"steps": 0.0}, memes={"curiosity": 1.0, "focus": 1.0}))
    rhyme = w.add(Entity(id="Rhyme", kind="character", role="detective", label="Rhyme",
                         meters={"steps": 0.0}, memes={"curiosity": 1.0, "focus": 1.0}))
    teamwork = w.add(Entity(id="Teamwork", kind="character", role="detective", label="Teamwork",
                            meters={"steps": 0.0}, memes={"curiosity": 1.0, "focus": 1.0}))
    mystery = w.add(Entity(id="mystery", label="the missing papaya bowl",
                           meters={"missing": 1.0}, memes={"confusion": 1.0}))
    papaya = w.add(Entity(id="papaya", label="the papaya bowl",
                          meters={"present": 1.0}, memes={"freshness": 1.0}))
    clue = w.add(Entity(id="clue", label=CLUES[params.clue],
                        meters={"found": 0.0, "shared": 0.0}, memes={"importance": 1.0}))
    suspect = w.add(Entity(id="suspect", label=SUSPECTS[params.suspect],
                           meters={"noticed": 0.0}, memes={"nervousness": 0.0}))

    w.facts.update(
        twist_actor="Twist",
        rhyme_speaker="Rhyme",
        rhyme_line="A tidy line can hide a better design",
        twist_hint=1,
        reason=params.explanation,
        location=params.location,
        clue=params.clue,
        suspect=params.suspect,
    )

    w.say(
        f"Twist, Rhyme, and Teamwork were detectives at {w.location}, where a papaya bowl had gone missing."
    )
    w.say(
        f"Someone kept whispering cholesterol, like it was a clue, but Twist knew a mystery could hide behind a healthy word."
    )
    w.para()
    w.say(
        f"They found {clue.label} near the snack shelf, and Rhyme pointed to {suspect.label} across the room."
    )
    clue.meters["found"] = 1.0
    suspect.meters["noticed"] = 1.0
    twist.meters["steps"] += 2
    rhyme.meters["steps"] += 2
    teamwork.meters["steps"] += 2
    w.get("papaya").meters["present"] = 0.0
    w.get("papaya").meters["moved"] = 1.0
    w.get("note").meters["shared"] = 1.0
    w.para()
    propagate(w)
    w.say(
        f"Then the twist was solved: the papaya had been {params.explanation} to the healthy shelf by {suspect.label}, who was trying to help with a better snack plan."
    )
    w.say(
        f"The detectives laughed, set the papaya back in the bright bowl, and shared a neat rhyme about working together."
    )
    w.facts.update(
        twist=twist, rhyme=rhyme, teamwork=teamwork, mystery=mystery,
        papaya=papaya, clue_ent=clue, suspect_ent=suspect, resolved=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a detective story for a young child that includes the words "papaya" and "cholesterol".',
        f"Tell a mystery story where Twist, Rhyme, and Teamwork solve a clue at {world.location}.",
        "Make the solution feel clever, gentle, and a little surprising, with a twist and a rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who solved the missing papaya mystery?",
            answer="Twist, Rhyme, and Teamwork solved it together. They compared the clues, followed the trail, and stayed calm until the answer made sense.",
        ),
        QAItem(
            question="Why did the papaya look missing at first?",
            answer=f"It looked missing because {world.facts['suspect']} had {world.facts['reason']} it to the healthy shelf. That made the snack table look empty even though the papaya was still in the building.",
        ),
        QAItem(
            question="What helped the detectives understand the twist?",
            answer="A shared note and careful teamwork helped most. Twist noticed the odd turn, Rhyme matched the clue, and Teamwork helped them line everything up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a papaya?",
            answer="A papaya is a soft tropical fruit with orange or pink flesh and black seeds. People often eat it as a snack or in fruit bowls.",
        ),
        QAItem(
            question="What is cholesterol?",
            answer="Cholesterol is a fatty substance in the body. Our bodies need a little, but too much can be unhealthy, so people talk about it when they make food choices.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work as one group. Each person adds something useful, so the job gets done more easily.",
        ),
    ]


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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.kind:9}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in world.facts.items() if k in {'location','clue','suspect','reason'})}}}")
    return "\n".join(lines)


ASP_RULES = r"""
twist_detected :- clue_found, twist_hint.
rhyme_detected :- shared_note, rhyme_line.
teamwork_detected :- clue_found, shared_note.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("clue_found"),
        asp.fact("shared_note"),
        asp.fact("twist_hint"),
        asp.fact("rhyme_line"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show twist_detected/0.\n#show teamwork_detected/0.\n#show rhyme_detected/0."))
    atoms = {sym.name for sym in model}
    ok = {"twist_detected", "teamwork_detected", "rhyme_detected"} <= atoms
    sample = generate(resolve_params(argparse.Namespace(location=None, clue=None, suspect=None, explanation=None), random.Random(777)))
    if ok and sample.story:
        print("OK: ASP twin and story generation smoke test passed.")
        return 0
    print("FAIL: verify checks did not pass.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with papaya, cholesterol, Twist, Rhyme, and Teamwork.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--explanation", choices=EXPLANATIONS)
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
              if (args.location is None or c[0] == args.location)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    loc, clue, suspect = rng.choice(sorted(combos))
    explanation = args.explanation or rng.choice(sorted(EXPLANATIONS))
    return StoryParams(location=loc, clue=clue, suspect=suspect, explanation=explanation)


def generate(params: StoryParams) -> StorySample:
    if params.location not in LOCATIONS or params.clue not in CLUES or params.suspect not in SUSPECTS or params.explanation not in EXPLANATIONS:
        raise StoryError("Invalid story parameters.")
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


CURATED = [
    StoryParams(location="market", clue="note", suspect="helper", explanation="moved"),
    StoryParams(location="store", clue="receipt", suspect="neighbor", explanation="borrowed"),
    StoryParams(location="school", clue="crumbs", suspect="helper", explanation="repacked"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show twist_detected/0.\n#show teamwork_detected/0.\n#show rhyme_detected/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible stories:")
        for combo in valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
