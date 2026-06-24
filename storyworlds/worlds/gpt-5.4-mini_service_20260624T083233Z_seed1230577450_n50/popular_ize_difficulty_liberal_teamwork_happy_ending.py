#!/usr/bin/env python3
"""
A small detective-story world with teamwork, foreshadowing, and a happy ending.

Premise:
A child detective notices something strange at a neighborhood festival: the
most loved banner has gone missing right before the big crowd arrives. The
search is not just about finding an object; it is about helping a community
keep a warm, welcoming celebration alive.

The domain uses three seed words as world vocabulary:
- popular-ize: a slogan that tries to make the festival feel widely loved
- difficulty: the trouble caused by the missing banner and confusing clues
- liberal: the name of the street where the festival takes place

The story engine models physical meters and emotional memes, with a small set
of characters and objects. Foreshadowing is used as a clue trail, teamwork as
the method, and a happy ending as the resolution.
"""

from __future__ import annotations

import argparse
import copy
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class CaseFile:
    id: str
    clue: str
    trouble: str
    solution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Help:
    id: str
    label: str
    action: str
    result: str
    fixes: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "liberal_street": Setting(place="Liberal Street", vibe="busy and bright", affords={"festival", "parade"}),
    "town_square": Setting(place="Town Square", vibe="open and echoing", affords={"festival", "parade"}),
    "school_hall": Setting(place="the school hall", vibe="quiet and warm", affords={"festival"}),
}

CASES = {
    "missing_banner": CaseFile(
        id="missing_banner",
        clue="a ribbon tied to the map table",
        trouble="the welcome banner was gone",
        solution="the banner was stuck behind the stage curtain",
        tags={"banner", "clue", "popular-ize"},
    ),
    "muddy_boxes": CaseFile(
        id="muddy_boxes",
        clue="small muddy footprints near the supply box",
        trouble="the flyers were in a messy pile",
        solution="the flyers had been moved to dry shelves",
        tags={"clue", "difficulty"},
    ),
    "lost_keys": CaseFile(
        id="lost_keys",
        clue="a jingling sound under the bench",
        trouble="the supply cabinet could not be opened",
        solution="the keys were under a bench cloth",
        tags={"clue"},
    ),
}

HELPS = {
    "map": Help(
        id="map",
        label="a hand-drawn map",
        action="spread out the map and compare the clues",
        result="it showed a short path to the stage",
        fixes={"banner", "keys"},
    ),
    "flashlight": Help(
        id="flashlight",
        label="a small flashlight",
        action="shine the light into the dark corners",
        result="it made the curtain bumps easy to see",
        fixes={"banner"},
    ),
    "labels": Help(
        id="labels",
        label="colored labels",
        action="sort the papers with colored labels",
        result="the team could find the flyers fast",
        fixes={"flyers"},
    ),
}

ACTIVITIES = {
    "festival": "help with the festival",
    "parade": "watch the parade",
}

NAMES = ["Mina", "Eli", "Rosa", "Noah", "Lina", "Arlo", "Maya", "Theo"]
HELPERS = ["friend", "cousin", "neighbor"]


@dataclass
class StoryParams:
    setting: str
    case: str
    help_item: str
    name: str
    helper_role: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with teamwork and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--help-item", choices=HELPS)
    ap.add_argument("--name")
    ap.add_argument("--helper-role", choices=HELPERS)
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


def reasonableness_gate(setting: str, case: str, help_item: str) -> bool:
    return True if setting in SETTINGS and case in CASES and help_item in HELPS else False


ASP_RULES = r"""
setting(liberal_street). setting(town_square). setting(school_hall).
case(missing_banner). case(muddy_boxes). case(lost_keys).
help(map). help(flashlight). help(labels).

works(map, missing_banner).
works(flashlight, missing_banner).
works(labels, muddy_boxes).
valid(S,C,H) :- setting(S), case(C), help(H), works(H,C).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([asp.fact("setting", s) for s in SETTINGS] +
                     [asp.fact("case", c) for c in CASES] +
                     [asp.fact("help", h) for h in HELPS] +
                     [asp.fact("works", h.id, c.id) for h in HELPS.values() for c in CASES.values() if h.id in {"map", "flashlight"} and c.id == "missing_banner" or h.id == "labels" and c.id == "muddy_boxes"])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CASES:
            for h in HELPS:
                if (h, c) in {("map", "missing_banner"), ("flashlight", "missing_banner"), ("labels", "muddy_boxes")}:
                    out.append((s, c, h))
    return out


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.case is None or c[1] == args.case)
              and (args.help_item is None or c[2] == args.help_item)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, case, help_item = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper_role = args.helper_role or rng.choice(HELPERS)
    return StoryParams(setting=setting, case=case, help_item=help_item, name=name, helper_role=helper_role)


def _apply_clue(world: World, detective: Entity, clue: str) -> None:
    detective.memes["foreshadowing"] = detective.memes.get("foreshadowing", 0) + 1
    world.say(f"{detective.id} noticed {clue}, and it felt like a clue waiting to speak.")


def _teamwork(world: World, detective: Entity, helper: Entity, help_item: Help, case: CaseFile) -> None:
    detective.memes["trust"] = detective.memes.get("trust", 0) + 1
    helper.memes["helpful"] = helper.memes.get("helpful", 0) + 1
    world.say(f"Together, {detective.id} and {helper.id} used {help_item.label}; {help_item.action}.")
    world.say(f"That teamwork meant {help_item.result}.")


def _solve(world: World, detective: Entity, case: CaseFile, help_item: Help) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    world.say(f"At last, the mystery was solved: {case.solution}.")
    world.say(f"The big worry faded, and the whole street could smile again.")


def tell(setting: Setting, case: CaseFile, help_item: Help, name: str, helper_role: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type="girl", label=name))
    helper = world.add(Entity(id=helper_role, kind="character", type="child", label=helper_role))
    banner = world.add(Entity(id="banner", label="the welcome banner", phrase="the welcome banner", location=setting.place))
    world.facts.update(detective=detective, helper=helper, case=case, help_item=help_item, banner=banner)

    world.say(f"On {setting.place}, {name} was a small detective who liked patterns and quiet clues.")
    world.say(f"People said the festival would popular-ize the town, because the event made everyone feel welcome.")
    world.say(f"But that morning, there was difficulty: {case.trouble}.")
    world.para()
    _apply_clue(world, detective, case.clue)
    world.say(f"{name} looked twice at the ribbon and once at the dusty floor; the clue seemed important.")
    world.say(f"That was the kind of foreshadowing a detective notices before the answer appears.")
    world.para()
    world.say(f"{name} called on {helper_role} to help. {helper_role.capitalize()} did not solve it alone; they worked as a team.")
    _teamwork(world, detective, helper, help_item, case)
    _solve(world, detective, case, help_item)
    world.say(f"In the end, the banner was back where everyone could see it, and the festival felt cheerful and fair.")
    world.say(f"{name} laughed with {helper_role}, glad the mystery ended with a happy ending.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short detective story for a child about {f['detective'].id} solving a clue on {world.setting.place}.",
        f"Tell a story with foreshadowing, teamwork, and a happy ending where {f['help_item'].label} helps solve the mystery.",
        f"Write a gentle mystery that uses the word popular-ize and ends with the problem being fixed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    case = f["case"]
    help_item = f["help_item"]
    return [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is {detective.id}, who watches carefully and follows clues.",
        ),
        QAItem(
            question=f"What was the difficulty at the start?",
            answer=f"The difficulty was that {case.trouble}.",
        ),
        QAItem(
            question=f"How did {detective.id} and {helper.id} fix the mystery?",
            answer=f"They used {help_item.label} and worked together, so the answer became clear.",
        ),
        QAItem(
            question=f"What proved the story had a happy ending?",
            answer=f"The banner was found again, and everyone could enjoy the festival with relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does teamwork mean?", answer="Teamwork means people help each other and do a job together."),
        QAItem(question="What is foreshadowing in a story?", answer="Foreshadowing is a clue that hints at what will happen later."),
        QAItem(question="What is a happy ending?", answer="A happy ending is when the problem gets solved and the characters feel glad."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CASES[params.case], HELPS[params.help_item], params.name, params.helper_role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="liberal_street", case="missing_banner", help_item="map", name="Mina", helper_role="friend"),
    StoryParams(setting="town_square", case="missing_banner", help_item="flashlight", name="Eli", helper_role="cousin"),
    StoryParams(setting="school_hall", case="muddy_boxes", help_item="labels", name="Rosa", helper_role="neighbor"),
]


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for t in vals:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
            p = sample.params
            header = f"### {p.name}: {p.case} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
