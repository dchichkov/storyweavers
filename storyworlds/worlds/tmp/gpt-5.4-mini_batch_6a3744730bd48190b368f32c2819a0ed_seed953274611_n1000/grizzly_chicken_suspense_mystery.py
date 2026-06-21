#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grizzly_chicken_suspense_mystery.py
====================================================================

A small standalone storyworld for a suspenseful mystery with the seed words
"grizzly" and "chicken".

Premise:
A child spots strange tracks, hears a chicken clucking at night, and worries a
grizzly bear may be nearby. The mystery resolves when the clues are explained
and the chicken is revealed as the source of the noise, while the bear turns out
to be harmlessly distant or only a mistaken shape. The story should feel tense,
child-facing, concrete, and resolved by careful noticing.

This file follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    dark_place: str
    sound_source: str
    mist: str


@dataclass
class Clue:
    id: str
    label: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    truth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    calm: int
    method: str
    text: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_nervous(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["mystery"] < THRESHOLD or e.meters["fear"] >= THRESHOLD:
            continue
        sig = ("nervous", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["alert"] += 1
        out.append("__narrate__")
    return out


def _r_clued(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["clue"] < THRESHOLD:
            continue
        sig = ("clued", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["certainty"] += 1
        out.append("__narrate__")
    return out


CAUSAL_RULES = [Rule("nervous", _r_nervous), Rule("clued", _r_clued)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mystery_at_risk(setting: Setting, clue: Clue, suspect: Suspect) -> bool:
    return "night" in setting.id and "tracks" in clue.tags and "bear" in suspect.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.calm >= 2]


def outcome_of(params: "StoryParams") -> str:
    if params.mindful:
        return "solved"
    if params.delay >= 2:
        return "spooked"
    return "solved"


def _do_mystery(world: World, clue: Clue) -> None:
    world.get("child").meters["mystery"] += 1
    world.get("child").meters["clue"] += 1
    propagate(world, narrate=False)


def tell(setting: Setting, clue: Clue, suspect: Suspect, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother", mindful: bool = True, delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="observer"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="helper"))
    grizzly = world.add(Entity(id="grizzly", kind="character", type="thing", label="grizzly", role="suspect", traits=["big"]))
    chicken = world.add(Entity(id="chicken", kind="character", type="thing", label="chicken", role="clue-source"))
    child.memes["curiosity"] = 1.0
    world.say(
        f"One evening, {child.id} stood at {setting.place} and noticed something odd in the dim light."
    )
    world.say(
        f"Near {setting.dark_place}, there were marks in the dirt and a small noise coming from the pen."
    )
    world.para()
    world.say(f"{child.id} heard a soft cluck from the {setting.sound_source} and felt a shiver of suspense.")
    world.say(f"At the same time, a thought of a {suspect.label} made the shadows seem bigger.")

    if mindful:
        world.para()
        world.say(
            f'"{suspect.label}?" {child.id} whispered, but {parent.label_word} bent down and looked closely.'
        )
        world.say(
            f'"Wait," said {parent.label_word}. "{clue.label} are from the chicken, not a hidden monster."'
        )
        world.say(
            f"With a careful lamp and a slow step, they followed the clue and found the chicken pecking by the fence."
        )
        world.say(
            f"The grizzly was only a far-off shape in the dusk, and the real mystery was solved by noticing the little details."
        )
        child.memes["relief"] += 1
        parent.memes["pride"] += 1
    else:
        world.para()
        world.say(
            f"{child.id} backed up fast and called for {parent.label_word}, because the dark shape looked like a {suspect.label}."
        )
        if delay >= 2:
            world.say(
                f"For a tense moment, nobody knew what was hidden in the mist, and the whole yard felt too quiet."
            )
        world.say(
            f"{parent.label_word} came quickly, lifted the lamp, and showed that the sound was only the chicken in its little coop."
        )
        world.say(
            f"The grizzly was never close; the fear came from a shadow and a guess, and the night grew calm again."
        )
        child.memes["relief"] += 1
        child.memes["fear"] += 1

    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        clue=clue,
        suspect=suspect,
        response=response,
        mindful=mindful,
        delay=delay,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the words "{f["suspect"].label}" and "chicken".',
        f"Tell a suspenseful story where {f['child'].id} hears a chicken at {f['setting'].place} and worries about a {f['suspect'].label}, but the mystery gets solved by careful noticing.",
        f"Write a gentle mystery with suspense, clues, and a calm ending set near {f['setting'].dark_place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    clue = f["clue"]
    suspect = f["suspect"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who was trying to understand a strange noise at {setting.place}. {parent.label_word} helps by looking at the clues too."),
        ("What made the story feel suspenseful?",
         f"A cluck in the dark and marks near {setting.dark_place} made {child.id} nervous. It felt suspenseful because the clues seemed to point toward a {suspect.label}."),
        ("What was the chicken doing?",
         f"The chicken was making the little noise that scared everyone. In the end, the chicken was simply pecking by its coop and was not the danger."),
        ("How did they solve the mystery?",
         f"They looked at the clue carefully instead of guessing. That helped them see that the sound came from the chicken, while the {suspect.label} was only a far-off shape."),
    ]
    if f["mindful"]:
        qa.append((
            "How did the story end?",
            f"It ended calmly, with the mystery solved and the fear gone. The family learned that careful looking can make a scary night feel safe again."
        ))
    else:
        qa.append((
            "Why did {0} feel relieved at the end?".format(child.id),
            f"{child.id} felt relieved because {parent.label_word} explained the clue and showed the chicken. The scary guess about the {suspect.label} turned out to be wrong."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["clue"].tags) | set(world.facts["suspect"].tags) | {"mystery", "suspense"}
    out: list[tuple[str, str]] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
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
    for e in world.entities.values():
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


SETTINGS = {
    "night_yard": Setting(id="night_yard", place="the backyard at night", dark_place="the shed door", sound_source="chicken coop", mist="mist"),
    "barn_path": Setting(id="barn_path", place="the barn path", dark_place="the tall weeds", sound_source="chicken pen", mist="fog"),
    "orchard": Setting(id="orchard", place="the orchard", dark_place="the old apple tree", sound_source="henhouse", mist="shadow"),
}

CLUES = {
    "tracks": Clue(id="tracks", label="tracks", reveal="little prints in the dirt", tags={"tracks", "mystery"}),
    "feathers": Clue(id="feathers", label="feathers", reveal="soft white feathers on the gate", tags={"mystery"}),
    "cluck": Clue(id="cluck", label="a cluck", reveal="a cluck from the coop", tags={"mystery", "suspense"}),
}

SUSPECTS = {
    "grizzly": Suspect(id="grizzly", label="grizzly", truth="a bear far beyond the fence", tags={"bear", "grizzly"}),
    "shadow": Suspect(id="shadow", label="shadow", truth="a shadow from a post and a tree", tags={"shadow"}),
}

RESPONSES = {
    "lamp": Response(id="lamp", calm=3, method="lift the lamp", text="lifted the lamp and followed the clue", tags={"lamp"}),
    "count": Response(id="count", calm=2, method="count the prints", text="counted the prints slowly until the answer made sense", tags={"count"}),
    "call_parent": Response(id="call_parent", calm=3, method="call a parent", text="called the parent and waited for a careful look", tags={"call"}),
}

class StoryParams:
    pass
@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    response: str
    child_name: str
    child_gender: str
    parent: str
    mindful: bool = True
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for suid, suspect in SUSPECTS.items():
                if mystery_at_risk(setting, clue, suspect):
                    combos.append((sid, cid, suid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful mystery storyworld about a chicken, a grizzly, and careful noticing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--mindful", action="store_true", default=False)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.setting and args.clue and args.suspect:
        if not mystery_at_risk(SETTINGS[args.setting], CLUES[args.clue], SUSPECTS[args.suspect]):
            raise StoryError("That combination doesn't make a real mystery.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Eli", "Nora", "Theo", "June", "Sam"])
    parent = args.parent or rng.choice(["mother", "father"])
    mindful = args.mindful or rng.choice([True, True, False])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting, clue=clue, suspect=suspect, response=response,
        child_name=name, child_gender=gender, parent=parent, mindful=mindful, delay=delay
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.suspect not in SUSPECTS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    world = tell(
        SETTINGS[params.setting], CLUES[params.clue], SUSPECTS[params.suspect], RESPONSES[params.response],
        child_name=params.child_name, child_gender=params.child_gender, parent_type=params.parent,
        mindful=params.mindful, delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for suid in SUSPECTS:
        lines.append(asp.fact("suspect", suid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,U) :- setting(S), clue(C), suspect(U), S = S, C = C, U = U.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, suspect=None, response=None, name=None, gender=None, parent=None, mindful=False, delay=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


CURATED = [
    StoryParams(setting="night_yard", clue="tracks", suspect="grizzly", response="lamp", child_name="Mina", child_gender="girl", parent="mother", mindful=True, delay=0),
    StoryParams(setting="barn_path", clue="cluck", suspect="grizzly", response="call_parent", child_name="Eli", child_gender="boy", parent="father", mindful=False, delay=1),
]


def explain_rejection() -> str:
    return "That mix does not create a believable mystery."


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} compatible mysteries:")
        for t in asp.atoms(model, "valid"):
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
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
