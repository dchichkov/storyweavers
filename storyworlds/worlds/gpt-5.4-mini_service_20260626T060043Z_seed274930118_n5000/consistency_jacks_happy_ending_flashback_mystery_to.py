#!/usr/bin/env python3
"""
storyworlds/worlds/consistency_jacks_happy_ending_flashback_mystery_to.py
========================================================================

A small space-adventure storyworld about a child crew, a puzzling machine,
a flashback clue, and a happy ending that proves the mystery was solved with
care and consistency.

Premise used to build the world model:
- A young astronaut loves helping in a little starport.
- A docking problem appears: a set of "jacks" on a cargo cradle will not
  line up the same way twice.
- The crew remembers a flashback about a tiny sticker on a lever.
- They solve the mystery by staying consistent, checking each jack in order,
  and restoring the ship to a safe, happy ending.

The story is generated from the live world state: entity meters track
repair progress, confusion, trust, and relief; the final prose reflects what
actually changed.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the starport bay"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Job:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    surprise: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fits: str
    helps: set[str]
    careful: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_seen = False
        self.mystery_solved = False
        self.used_order: list[str] = []

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.flashback_seen = self.flashback_seen
        clone.mystery_solved = self.mystery_solved
        clone.used_order = list(self.used_order)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "starport": Setting(place="the starport bay", indoors=True, affords={"jacks", "lights"}),
    "hangar": Setting(place="the hangar", indoors=True, affords={"jacks", "cables"}),
    "orbital_lab": Setting(place="the orbital lab", indoors=True, affords={"jacks", "screens"}),
}

JOBS = {
    "jacks": Job(
        id="jacks",
        verb="check the docking jacks",
        gerund="checking the docking jacks",
        rush="dash to the jacks",
        mess="misalignment",
        surprise="one jack was turned the wrong way",
        keyword="jacks",
        tags={"jacks", "repair"},
    ),
    "lights": Job(
        id="lights",
        verb="fix the blinking lights",
        gerund="fixing the blinking lights",
        rush="run to the light panel",
        mess="glitch",
        surprise="a lamp kept blinking in a strange pattern",
        keyword="lights",
        tags={"lights"},
    ),
    "cables": Job(
        id="cables",
        verb="sort the floating cables",
        gerund="sorting the floating cables",
        rush="reach for the cable tray",
        mess="tangle",
        surprise="the cables were knotted like a tiny maze",
        keyword="cables",
        tags={"cables"},
    ),
    "screens": Job(
        id="screens",
        verb="read the status screens",
        gerund="reading the status screens",
        rush="step over to the display wall",
        mess="confusion",
        surprise="the numbers did not agree with each other",
        keyword="screens",
        tags={"screens"},
    ),
}

TOOLS = {
    "spanner": Tool(
        id="spanner",
        label="a silver spanner",
        phrase="a silver spanner with a red grip",
        fits="jacks",
        helps={"misalignment"},
        careful="tightened each jack one by one",
        tags={"jacks", "repair"},
    ),
    "diagnostic_glass": Tool(
        id="diagnostic_glass",
        label="a diagnostic glass",
        phrase="a small diagnostic glass",
        fits="screens",
        helps={"confusion"},
        careful="made the tiny marks easy to read",
        tags={"screens"},
    ),
    "tape_tag": Tool(
        id="tape_tag",
        label="a bright tape tag",
        phrase="a bright tape tag",
        fits="cables",
        helps={"tangle"},
        careful="marked each cable in the same order every time",
        tags={"cables", "consistency"},
    ),
}

NAMES = ["Ari", "Mika", "Nova", "Pip", "Luna", "Tess", "Juno", "Kai"]
ROLES = ["girl", "boy"]
PARENTS = ["captain", "pilot", "mother", "father"]
TRAITS = ["careful", "curious", "brave", "steady", "patient"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    job: str
    tool: str
    name: str
    role: str
    parent_role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for job_id in setting.affords:
            job = JOBS[job_id]
            for tool_id, tool in TOOLS.items():
                if tool.fits == job_id and job.mess in tool.helps:
                    out.append((place, job_id, tool_id))
    return out


def explain_invalid(job: Job, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not actually solve the {job.keyword} mystery. "
        f"The tool must fit the same machine part and help with the right problem.)"
    )


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    job = JOBS[params.job]
    tool = TOOLS[params.tool]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.role, meters={}, memes={}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_role, label=f"the {params.parent_role}"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the little ship"))
    jacks = world.add(Entity(id="jacks", kind="thing", type="machine", label="the docking jacks", plural=True))
    clue = world.add(Entity(id="clue", kind="thing", type="sticker", label="a tiny sticker", phrase="a tiny sticker shaped like a star"))
    tool_ent = world.add(Entity(
        id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id
    ))

    hero.meters.update({"focus": 0.0, "confusion": 0.0, "repair": 0.0, "joy": 0.0, "relief": 0.0})
    hero.memes.update({"hope": 0.0, "trust": 0.0, "surprise": 0.0})
    parent.meters.update({"calm": 0.0, "worry": 0.0})
    ship.meters.update({"safe": 0.0, "threat": 0.0})
    jacks.meters.update({"alignment": 0.0, "stuck": 0.0})
    clue.meters.update({"noticed": 0.0})

    world.facts.update(
        hero=hero, parent=parent, ship=ship, jacks=jacks, clue=clue, tool=tool_ent,
        job=job, tool_def=tool, setting=setting, params=params
    )

    # Act 1: setup
    world.say(
        f"{hero.id} was a {params.trait} little {params.role} who loved the bright hum of {setting.place}."
    )
    world.say(
        f"{hero.id} liked helping the {params.parent_role} with small jobs on the ship, because every good fix made the bay feel safer."
    )
    world.say(
        f"One day, the ship had a problem with the {job.keyword}: {job.surprise}."
    )
    parent.meters["worry"] += 1
    jacks.meters["stuck"] += 1
    hero.meters["confusion"] += 1
    hero.memes["surprise"] += 1

    # Act 2: flashback clue
    world.para()
    world.say(
        f"{hero.id} stared at the machine, but the answer felt slippery. {hero.pronoun().capitalize()} could not tell why the same step worked one moment and failed the next."
    )
    world.say(
        f"Then a flashback floated into {hero.pronoun('possessive')} mind: yesterday, {hero.id} had seen {clue.phrase} stuck near the lever panel."
    )
    world.flashback_seen = True
    clue.meters["noticed"] = 1

    world.say(
        f"In the flashback, the sticker had pointed to the leftmost jack first, then the next one, and then the last one. The order mattered."
    )
    world.say(
        f"{hero.id} remembered that the best repairs were done the same careful way every time."
    )
    hero.meters["focus"] += 1
    hero.memes["trust"] += 1

    # Act 3: mystery solved consistently
    world.para()
    world.say(
        f"{hero.id} picked up {tool.label} and used it with steady hands."
    )
    world.say(
        f"{hero.id} did not hurry or skip steps. {hero.pronoun().capitalize()} checked the jacks one by one in the same order the flashback showed."
    )
    world.used_order = ["left", "middle", "right"]
    jacks.meters["alignment"] += 1
    hero.meters["repair"] += 1
    hero.meters["focus"] += 1

    if job.id == "jacks":
        world.say(
            f"The left jack clicked, then the middle one matched it, and the right one settled into place."
        )
    else:
        world.say(
            f"The strange problem softened as the same careful method revealed the hidden mistake."
        )

    world.say(
        f"At last, {tool.careful}, and the ship answered with a soft, happy chime."
    )
    ship.meters["safe"] += 1
    ship.meters["threat"] = 0
    parent.meters["worry"] = 0
    parent.meters["calm"] += 1
    hero.meters["joy"] += 1
    hero.meters["relief"] += 1
    hero.memes["hope"] += 1

    world.say(
        f"{hero.id} grinned as the bay lights warmed up again. The mystery was solved, the ship was safe, and the little crew could fly on."
    )
    world.mystery_solved = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a small child about {f["hero"].id}, a mystery with {f["job"].keyword}, and a happy ending.',
        f"Tell a gentle story where a young astronaut remembers a flashback clue and solves a problem with {f['tool_def'].label}.",
        f'Write a simple story that includes the word "{f["job"].keyword}" and shows how consistency helps fix a ship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    job = f["job"]
    tool = f["tool_def"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"What mystery did {hero.id} have to solve at {setting.place}?",
            answer=f"{hero.id} had to solve a problem with the {job.keyword}. {job.surprise.capitalize()} made the job puzzling at first.",
        ),
        QAItem(
            question=f"What flashback helped {hero.id} remember what to do?",
            answer=(
                f"{hero.id} remembered a flashback about {f['clue'].phrase} near the lever panel. "
                f"It showed that the jacks had to be checked in the same careful order every time."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} use {tool.label} to fix the problem?",
            answer=(
                f"{hero.id} used {tool.label} with steady hands and checked each jack one by one. "
                f"That consistency helped the ship line up and turn safe again."
            ),
        ),
        QAItem(
            question=f"Why did the {parent.type} stop worrying at the end?",
            answer=(
                f"The {parent.type} stopped worrying because the mystery was solved, the ship was safe, "
                f"and {hero.id} found a happy ending for the whole crew."
            ),
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "jacks": [
        (
            "What are docking jacks for?",
            "Docking jacks help hold a ship steady so it can connect safely to another ship or station.",
        )
    ],
    "consistency": [
        (
            "What does consistency mean?",
            "Consistency means doing something in the same careful way again and again, which helps people make fewer mistakes.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a memory scene that shows something that happened earlier, which can help explain the present problem.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzling problem that needs clues and careful thinking to solve.",
        )
    ],
    "ship": [
        (
            "Why do space crews check their ships?",
            "Space crews check their ships so everything stays safe and works the way it should during a flight.",
        )
    ],
}
WORLD_ORDER = ["consistency", "flashback", "mystery", "jacks", "ship"]


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["job"].tags) | {"consistency", "flashback", "mystery", "ship"}
    out: list[QAItem] = []
    for key in WORLD_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[key])
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    lines.append(f"  mystery_solved={world.mystery_solved}")
    lines.append(f"  used_order={world.used_order}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A job is compatible with a tool when the tool fits the same part and helps
% with the same problem kind.
compatible(J, T) :- job(J), tool(T), fits(T, J), helps(T, M), job_mess(J, M).

valid_story(P, J, T) :- place(P), affords(P, J), compatible(J, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for jid, job in JOBS.items():
        lines.append(asp.fact("job", jid))
        lines.append(asp.fact("job_mess", jid, job.mess))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("fits", tid, tool.fits))
        for m in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.job and args.tool:
        job, tool = JOBS[args.job], TOOLS[args.tool]
        if not (tool.fits == job.id and job.mess in tool.helps):
            raise StoryError(explain_invalid(job, tool))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.job is None or c[1] == args.job)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, job_id, tool_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    parent_role = args.parent_role or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, job=job_id, tool=tool_id, name=name, role=role, parent_role=parent_role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="starport", job="jacks", tool="spanner", name="Nova", role="girl", parent_role="captain", trait="careful"),
    StoryParams(place="hangar", job="cables", tool="tape_tag", name="Kai", role="boy", parent_role="pilot", trait="steady"),
    StoryParams(place="orbital_lab", job="screens", tool="diagnostic_glass", name="Luna", role="girl", parent_role="mother", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure storyworld: consistency, jacks, flashback clue, mystery, happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--parent-role", choices=PARENTS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, job, tool) combos:")
        for place, job, tool in combos:
            print(f"  {place:12} {job:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.job} at {p.place} using {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
