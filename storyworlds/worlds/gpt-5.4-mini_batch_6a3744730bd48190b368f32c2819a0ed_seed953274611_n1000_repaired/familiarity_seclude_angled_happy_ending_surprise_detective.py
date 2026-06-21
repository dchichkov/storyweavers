#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/familiarity_seclude_angled_happy_ending_surprise_detective.py
==============================================================================================

A small standalone story world for a child-facing detective story.

Seed premise:
- a young detective notices something familiar is missing,
- a clue leads them to seclude themselves in a small hidden place,
- an angled object reveals the surprise,
- the story ends happily with the lost thing found and the mystery solved.

This world keeps the prose concrete and state-driven, with a short causal model:
familiarity helps identify what's out of place, secluding a clue changes what can
be seen, and an angled view exposes the final hiding spot.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    hidden: bool = False
    angled: bool = False
    secluded: bool = False
    clue: bool = False
    surprise: bool = False

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    opening: str
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


@dataclass
class CaseFile:
    id: str
    mystery: str
    familiar_item: str
    missing_item: str
    hiding_spot: str
    angled_object: str
    reveal_method: str
    surprise_item: str
    ending_image: str
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


@dataclass
class StoryParams:
    setting: str
    casefile: str
    detective_name: str
    detective_gender: str
    partner_name: str
    partner_gender: str
    helper_role: str
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


class World:
    def __init__(self, setting: Setting, casefile: CaseFile) -> None:
        self.setting = setting
        self.casefile = casefile
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting, self.casefile)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_confidence(world: World) -> list[str]:
    out: list[str] = []
    det = world.get("detective")
    if det.memes["familiarity"] >= THRESHOLD and ("confidence", det.id) not in world.fired:
        world.fired.add(("confidence", det.id))
        det.memes["focus"] += 1
        out.append("")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    hide = world.get("hideout")
    if clue.secluded and clue.angled and hide.hidden and ("reveal", clue.id) not in world.fired:
        world.fired.add(("reveal", clue.id))
        hide.hidden = False
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("confidence", _r_confidence), Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_reveal(world: World) -> bool:
    sim = world.copy()
    sim.get("clue").secluded = True
    sim.get("clue").angled = True
    propagate(sim, narrate=False)
    return not sim.get("hideout").hidden


def tell(setting: Setting, casefile: CaseFile, params: StoryParams) -> World:
    world = World(setting, casefile)
    det = world.add(Entity(
        id="detective", kind="character", type=params.detective_gender,
        label=params.detective_name, role="detective", traits=["curious", "observant"],
    ))
    partner = world.add(Entity(
        id="partner", kind="character", type=params.partner_gender,
        label=params.partner_name, role=params.helper_role, traits=["brave", "kind"],
    ))
    case = world.add(Entity(
        id="casefile", kind="thing", type="thing", label=casefile.mystery
    ))
    clue = world.add(Entity(
        id="clue", kind="thing", type="thing", label=casefile.angled_object,
        clue=True, secluded=True, angled=False,
    ))
    hideout = world.add(Entity(
        id="hideout", kind="place", type="place", label=casefile.hiding_spot,
        hidden=True
    ))
    lost = world.add(Entity(
        id="lost", kind="thing", type="thing", label=casefile.missing_item,
        surprise=True
    ))
    familiar = world.add(Entity(
        id="familiar", kind="thing", type="thing", label=casefile.familiar_item
    ))

    det.memes["familiarity"] = 1.0
    partner.memes["hope"] = 1.0

    world.say(f"{setting.opening} {params.detective_name} knew the hallway with easy familiarity, and {params.partner_name} carried the case like a tiny treasure.")
    world.say(f'"Someone took {casefile.missing_item}," {params.partner_name} said. "We have to solve it."')

    world.para()
    world.say(f"{params.detective_name} looked around the room like a proper detective. The {casefile.familiar_item} on the shelf felt familiar, but one thing was missing.")
    world.say(f"Their first clue was {casefile.angled_object}, which leaned at a funny angle near {casefile.hiding_spot}.")
    if predict_reveal(world):
        world.say(f'{params.detective_name} smiled. "If we seclude the clue where the light is sharp and turn it angled, it might show us more."')
    else:
        world.say(f'{params.partner_name} frowned. "That clue is not enough by itself."')

    world.para()
    clue.angled = True
    clue.secluded = True
    det.memes["familiarity"] += 1
    det.memes["hope"] += 1
    world.say(f"{params.detective_name} tucked everyone into a quiet corner to seclude the clue from the busy room, then tilted it just right.")
    propagate(world, narrate=False)
    if hideout.hidden:
        world.say(f"At first, the hiding spot stayed tucked away, like a secret behind a curtain.")
    else:
        world.say(f"Then the angled clue flashed a surprising reflection, and the hidden spot opened the mystery at once.")

    world.para()
    hideout.hidden = False
    lost.hidden = False
    det.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(f"Inside {casefile.hiding_spot}, they found {casefile.surprise_item} hiding beside {casefile.missing_item}. It was the surprise nobody expected.")
    world.say(f"{params.partner_name} laughed in relief, and {params.detective_name} solved the case with a grin.")
    world.say(f"The ending looked just like this: {casefile.ending_image}")

    world.facts.update(
        detective=det,
        partner=partner,
        casefile=case,
        clue=clue,
        hideout=hideout,
        lost=lost,
        familiar=familiar,
        setting=setting,
        case_def=casefile,
        revealed=not hideout.hidden,
        surprise_found=True,
    )
    return world


SETTINGS = {
    "library": Setting(
        id="library",
        place="the old library",
        mood="quiet",
        opening="In the quiet old library, the lamps glowed gold between tall shelves."
    ),
    "museum": Setting(
        id="museum",
        place="the small museum",
        mood="careful",
        opening="At the small museum, the rooms were neat and still, with bright signs on the walls."
    ),
    "garden": Setting(
        id="garden",
        place="the back garden",
        mood="soft",
        opening="In the back garden, the hedges made a calm maze of green paths."
    ),
}

CASEFILES = {
    "missing_lantern": CaseFile(
        id="missing_lantern",
        mystery="the missing lantern",
        familiar_item="desk lamp",
        missing_item="little lantern",
        hiding_spot="the angled umbrella stand",
        angled_object="an angled mirror",
        reveal_method="tilt the mirror",
        surprise_item="a note from Grandma",
        ending_image="A little lantern glowed on the table while the note from Grandma sat beside it, all safe and bright."
    ),
    "missing_cookie_tin": CaseFile(
        id="missing_cookie_tin",
        mystery="the missing cookie tin",
        familiar_item="tea tray",
        missing_item="cookie tin",
        hiding_spot="the slanted cart corner",
        angled_object="an angled picture frame",
        reveal_method="tilt the frame",
        surprise_item="a stray ribbon",
        ending_image="The cookie tin sat open on the windowsill, with a ribbon peeking out and sunshine on the lid."
    ),
    "missing_key": CaseFile(
        id="missing_key",
        mystery="the missing brass key",
        familiar_item="brass knob",
        missing_item="brass key",
        hiding_spot="the sloped book cart",
        angled_object="an angled clock face",
        reveal_method="tilt the clock",
        surprise_item="a toy mouse",
        ending_image="The brass key hung from a hook, and the toy mouse sat neatly in a basket under the clock."
    ),
}

DETECTIVE_NAMES = ["Milo", "Nina", "Tessa", "Arlo", "June", "Iris", "Ezra", "Maya"]
PARTNER_NAMES = ["Pip", "Lena", "Owen", "Bea", "Noah", "Rae", "Theo", "Cora"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CASEFILES]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the words "familiarity", "seclude", and "angled".',
        f"Tell a happy-ending mystery where {f['detective'].label} and {f['partner'].label} solve the case by using a clue that looks angled.",
        f"Write a surprise-filled detective story in {f['setting'].place} where a familiar object helps find something missing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det = f["detective"]
    partner = f["partner"]
    case = f["case_def"]
    return [
        ("Who solved the mystery?",
         f"{det.label} solved it with help from {partner.label}. They worked together and followed the clue until the hiding place was found."),
        ("What made the clue useful?",
         f"The clue was angled, so it stood out once they secluded it from the busy room. That careful look let them see the hidden spot more clearly."),
        ("What was the surprise?",
         f"The surprise was {case.surprise_item}, found beside {case.missing_item}. Nobody expected it, which made the ending a happy one."),
        ("How did the story end?",
         f"It ended happily. The missing thing was found, the surprise was explained, and the final picture was {case.ending_image}"),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a detective do?",
         "A detective looks for clues and asks careful questions to solve a mystery. They notice small details that other people might miss."),
        ("What is a clue?",
         "A clue is a small bit of information that helps solve a mystery. It can be an object, a mark, or something that looks out of place."),
        ("What does it mean to seclude something?",
         "To seclude something means to put it in a quiet or hidden place away from a crowd. That can make it easier to study carefully."),
        ("What does angled mean?",
         "Angled means turned slantwise instead of straight. An angled thing can catch the light or stand out in a helpful way."),
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
        flags = []
        if e.hidden:
            flags.append("hidden")
        if e.angled:
            flags.append("angled")
        if e.secluded:
            flags.append("secluded")
        if e.clue:
            flags.append("clue")
        if e.surprise:
            flags.append("surprise")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
familiarity_boost(D) :- detective(D), familiarity(D, F), F >= 1.
reveal(H) :- clue(C), hidden(H), secluded(C), angled(C).
happy_ending :- reveal(_).
surprise_found :- surprise(S), found(S).
valid_story(Setting, Case) :- setting(Setting), case(Case).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASEFILES:
        lines.append(asp.fact("case", cid))
    lines.append(asp.fact("threshold", THRESHOLD))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    try:
        import asp
        expected = set(valid_combos())
        actual = set(asp_valid_combos())
        rc = 0
        if expected == actual:
            print(f"OK: ASP matches valid_combos() ({len(actual)} combos).")
        else:
            print("MISMATCH in valid combos.")
            if actual - expected:
                print("  only in ASP:", sorted(actual - expected))
            if expected - actual:
                print("  only in Python:", sorted(expected - actual))
            rc = 1
        sample = generate(StoryParams(
            setting="library",
            casefile="missing_lantern",
            detective_name="Milo",
            detective_gender="boy",
            partner_name="Pip",
            partner_gender="girl",
            helper_role="helper",
            seed=1,
        ))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
        return rc
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with familiarity, seclude, and angled clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--casefile", choices=CASEFILES)
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", default="helper")
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.casefile and args.casefile not in CASEFILES:
        raise StoryError("Unknown case file.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.casefile is None or c[1] == args.casefile)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, casefile = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if gender == "girl" else "girl")
    detective_name = args.name or rng.choice(DETECTIVE_NAMES)
    partner_name = args.partner or rng.choice(PARTNER_NAMES)
    return StoryParams(
        setting=setting,
        casefile=casefile,
        detective_name=detective_name,
        detective_gender=gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        helper_role=args.helper_role,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.casefile not in CASEFILES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], CASEFILES[params.casefile], params)
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


CURATED = [
    StoryParams(
        setting="library",
        casefile="missing_lantern",
        detective_name="Milo",
        detective_gender="boy",
        partner_name="Pip",
        partner_gender="girl",
        helper_role="helper",
        seed=1,
    ),
    StoryParams(
        setting="museum",
        casefile="missing_cookie_tin",
        detective_name="Nina",
        detective_gender="girl",
        partner_name="Owen",
        partner_gender="boy",
        helper_role="partner",
        seed=2,
    ),
    StoryParams(
        setting="garden",
        casefile="missing_key",
        detective_name="Arlo",
        detective_gender="boy",
        partner_name="Rae",
        partner_gender="girl",
        helper_role="helper",
        seed=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for s, c in combos:
            print(f"  {s:8} {c}")
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = "### story" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
