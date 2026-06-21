#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/natural_mystery_to_solve_mystery.py
====================================================================

A standalone storyworld for a small mystery domain with a natural, child-facing
solve-the-mystery arc.

Premise:
- A child notices something small and odd in a natural setting.
- The clue trail leads through a garden, path, or park.
- A helper follows evidence, not guesses.
- The mystery is solved by checking real world state: tracks, smells, objects
  moved, and ownership.
- The ending proves what changed by showing the recovered item or the revealed
  source.

The word "natural" is intentionally part of the domain vocabulary and the prose.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma",
                "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    natural: bool
    details: str
    clue_kind: str
    sounds: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mystery:
    id: str
    title: str
    thing: str
    missing: str
    found: str
    evidence: str
    source: str
    solution: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    plausible: bool
    clue: str
    truth: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_clue_bright(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["clue"] >= THRESHOLD and ("clue_bright", e.id) not in world.fired:
            world.fired.add(("clue_bright", e.id))
            world.get("detective").memes["focus"] += 1
            out.append(f"{world.get('detective').id} noticed that clue and kept looking carefully.")
    return out


def _r_truth_found(world: World) -> list[str]:
    out: list[str] = []
    if world.get("detective").memes["focus"] < THRESHOLD:
        return out
    if world.get("case").meters["solved"] >= THRESHOLD:
        return out
    if world.get("lead").meters["checked"] < THRESHOLD:
        return out
    sig = ("truth",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("case").meters["solved"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("clue_bright", "mind", _r_clue_bright),
    Rule("truth_found", "plot", _r_truth_found),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mystery_reasonable(m: Mystery, s: Setting, suspect: Suspect) -> bool:
    return s.natural and suspect.plausible


def clue_points_to_suspect(world: World, suspect: Suspect) -> bool:
    return suspect.id == world.facts.get("true_suspect")


def expected_solution(m: Mystery, suspect: Suspect) -> str:
    if suspect.id == "wind":
        return "The wind blew the seed packet off the bench."
    if suspect.id == "raccoon":
        return "A raccoon tipped the lid aside and dragged the shiny ribbon away."
    return "A grown-up had moved it to keep it safe."


def evidence_matches(world: World, suspect: Suspect) -> bool:
    return clue_points_to_suspect(world, suspect)


def setup_scene(world: World, kid: Entity, helper: Entity, mystery: Mystery, suspect: Suspect) -> None:
    kid.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On a quiet morning, {kid.id} and {helper.id} walked through {world.setting.place}. "
        f"The place felt {('natural' if world.setting.natural else 'plain')}, with {world.setting.details}."
    )
    world.say(
        f"Then {kid.id} stopped short. {mystery.title} was a mystery to solve."
    )
    world.say(
        f"The little thing was gone: {mystery.missing}. But there was one odd clue: {mystery.evidence}."
    )


def inspect_clue(world: World, kid: Entity, helper: Entity, mystery: Mystery) -> None:
    kid.memes["worry"] += 1
    world.say(
        f'{kid.id} pointed at the clue and whispered, "Something is missing." '
        f'{helper.id} knelt down to look with {kid.pronoun("object")}.'
    )
    world.say(
        f'"Let us follow the clue first," {helper.id} said. '
        f'"A real mystery is solved by looking, not guessing."'
    )


def test_lead(world: World, helper: Entity, suspect: Suspect) -> None:
    lead = world.get("lead")
    lead.meters["checked"] += 1
    world.say(
        f"{helper.id} checked the likely lead: {suspect.label}. "
        f"{suspect.clue}"
    )


def reveal(world: World, mystery: Mystery, suspect: Suspect) -> None:
    world.get("case").meters["solved"] += 1
    world.say(
        f"At last, the answer fit the clues. {mystery.solution}"
    )
    world.say(
        f"The missing {mystery.thing} was found again, and the whole trail made sense."
    )


def ending(world: World, kid: Entity, helper: Entity, mystery: Mystery) -> None:
    kid.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{kid.id} smiled and held the {mystery.found} close. "
        f"{helper.id} smiled too, happy that the natural clues had led to the truth."
    )
    world.say(
        f"By the end of the day, the mystery was solved, and {kid.id} knew to look carefully next time."
    )


def tell(setting: Setting, mystery: Mystery, suspect: Suspect,
         kid_name: str = "Mila", kid_type: str = "girl",
         helper_name: str = "Grandma", helper_type: str = "grandmother") -> World:
    world = World(setting)
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_type, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="case", type="case", label=mystery.title))
    world.add(Entity(id="lead", type="lead", label=mystery.evidence))
    world.facts["true_suspect"] = suspect.id

    setup_scene(world, kid, helper, mystery, suspect)
    world.para()
    inspect_clue(world, kid, helper, mystery)
    test_lead(world, helper, suspect)
    propagate(world, narrate=False)
    world.para()
    if evidence_matches(world, suspect):
        reveal(world, mystery, suspect)
    else:
        world.say(
            f"The clue did not match {suspect.label}, so {helper.id} kept looking until the answer made sense."
        )
        reveal(world, mystery, suspect)
    world.para()
    ending(world, kid, helper, mystery)

    world.facts.update(
        kid=kid, helper=helper, mystery=mystery, suspect=suspect, setting=setting,
        solved=world.get("case").meters["solved"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", True,
                      "bushes, a stone path, and a birdbath", "leaf", "soft rustling"),
    "park": Setting("park", "the park", True,
                    "tall grass, a bench, and a little pond", "track", "wind in the trees"),
    "backyard": Setting("backyard", "the backyard", True,
                        "a fence, a flower bed, and a small shed", "track", "birds chirping"),
}

MYSTERIES = {
    "seed_packet": Mystery(
        "seed_packet", "The Missing Seed Packet", "seed packet", "the seed packet",
        "the seed packet with the red flower picture", "a trail of tiny spilled seeds",
        "the wind", "The wind blew the seed packet off the bench.",
        tags={"seed", "wind", "natural"},
    ),
    "ribbon": Mystery(
        "ribbon", "The Vanished Ribbon", "ribbon", "the ribbon",
        "the blue ribbon tied to the basket", "small muddy paw prints",
        "the raccoon", "A raccoon tipped the lid aside and dragged the shiny ribbon away.",
        tags={"ribbon", "raccoon", "natural"},
    ),
    "snack": Mystery(
        "snack", "The Missing Snack", "snack", "the snack",
        "the apple slices in the little bowl", "crumbs on the stone path",
        "the squirrel", "A squirrel snatched the snack and ran up the tree.",
        tags={"snack", "squirrel", "natural"},
    ),
}

SUSPECTS = {
    "wind": Suspect("wind", "the wind", "cause", True, "The seeds were scattered along the path.", "wind"),
    "raccoon": Suspect("raccoon", "a raccoon", "animal", True, "The paws left muddy prints near the shed.", "raccoon"),
    "squirrel": Suspect("squirrel", "a squirrel", "animal", True, "Tiny crumbs were stuck under the bench.", "squirrel"),
}

KID_NAMES = ["Mila", "Noah", "Lena", "Theo", "Ivy", "Owen", "Zoe", "Finn"]
HELPER_NAMES = ["Grandma", "Grandpa", "Auntie", "Uncle"]

@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    suspect: str
    kid: str
    kid_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            for spid, sp in SUSPECTS.items():
                if mystery_reasonable(m, s, sp):
                    out.append((sid, mid, spid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small natural mystery-solving storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--kid")
    ap.add_argument("--kid-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["grandmother", "grandfather", "aunt", "uncle"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, suspect = rng.choice(sorted(combos))
    kid_type = args.kid_type or rng.choice(["girl", "boy"])
    kid = args.kid or rng.choice(KID_NAMES)
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting, mystery, suspect, kid, kid_type, helper, helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that uses the word "natural" and ends with the mystery solved.',
        f"Tell a gentle mystery about {f['kid'].id} and {f['helper'].id} in {f['setting'].place}, where a clue leads to the answer.",
        f"Write a small solve-the-mystery story about a missing {f['mystery'].thing} in a natural place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    s: Suspect = f["suspect"]
    k: Entity = f["kid"]
    h: Entity = f["helper"]
    return [
        QAItem(
            question="What was the mystery?",
            answer=f"The mystery was that {m.missing} was gone. The clue was {m.evidence}, which helped point toward the answer."
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"{h.id} followed the clue and checked the likely lead instead of guessing. That careful search matched the evidence and showed what really happened."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {m.found} found again and {k.id} smiling. The natural clues led all the way to the truth, so the mystery was solved."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does natural mean?",
            answer="Natural means found in nature, like plants, wind, animals, stones, and trees. It is something that comes from the real world, not from a machine."
        ),
        QAItem(
            question="Why do clues matter in a mystery?",
            answer="Clues matter because they help you figure out what happened. A good mystery can be solved by carefully looking at the evidence."
        ),
        QAItem(
            question="What should you do before you guess in a mystery?",
            answer="You should look closely and check the evidence first. Careful looking makes the answer more likely to be right."
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "seed_packet", "wind", "Mila", "girl", "Grandma", "grandmother"),
    StoryParams("park", "ribbon", "raccoon", "Owen", "boy", "Grandpa", "grandfather"),
    StoryParams("backyard", "snack", "squirrel", "Ivy", "girl", "Auntie", "aunt"),
]


def explain_rejection(setting: Setting, mystery: Mystery, suspect: Suspect) -> str:
    if not setting.natural:
        return "(No story: this world needs a natural setting for the clue trail to make sense.)"
    if not suspect.plausible:
        return "(No story: the suspect does not fit the clue, so the mystery would not be solveable.)"
    return "(No story: that combination does not make a clean mystery.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.natural:
            lines.append(asp.fact("natural", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
    for spid, sp in SUSPECTS.items():
        lines.append(asp.fact("suspect", spid))
        if sp.plausible:
            lines.append(asp.fact("plausible", spid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, P) :- setting(S), mystery(M), suspect(P), natural(S), plausible(P).
solved(P) :- valid(_, M, P), suspect(P).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, mystery=None, suspect=None, kid=None, kid_type=None,
            helper=None, helper_type=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], SUSPECTS[params.suspect],
                 params.kid, params.kid_type, params.helper, params.helper_type)
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
        print(asp_program(show="#show valid/3.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
