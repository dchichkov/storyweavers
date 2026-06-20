#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/penal_ize_load_emu_bad_ending_whodunit.py
=========================================================================

A small whodunit-style storyworld about a puzzling missing load near an emu,
where one choice can be penalized, clues are tracked in the simulated state, and
some scenarios end badly.

The domain is intentionally tiny:
- One child detective notices a missing load.
- An emu is present and can be blamed, protected, or misunderstood.
- The story turns on evidence, accusation, and the consequences of a mistaken
  judgment.
- The generated stories include a bad-ending branch where the wrong suspect is
  punished and the real problem remains unsolved.

This file is standalone and uses only the Python stdlib plus the shared
storyworld result containers.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    scene: str
    clue_spots: list[str]
    bad_fit: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Load:
    id: str
    label: str
    phrase: str
    size: str
    missing_from: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    alibi: str
    can_access: bool
    can_hide: bool
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    place: str
    load: str
    suspect: str
    ending: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


PLACES = {
    "barn": Place(
        "barn",
        "the barn",
        "a dusty barn with hay and old boards",
        ["hay loft", "feed bin", "loose boards"],
        "There are too many places for a clue to hide there.",
        {"barn", "hay", "farm"},
    ),
    "yard": Place(
        "yard",
        "the back yard",
        "a quiet back yard with a fence and a shed",
        ["shed step", "flower bed", "fence rail"],
        "The yard is too open and simple for this kind of mystery.",
        {"yard", "fence", "shed"},
    ),
    "coop": Place(
        "coop",
        "the chicken coop",
        "a cramped chicken coop with straw and a small door",
        ["straw corner", "door latch", "water tray"],
        "The coop makes the clues too obvious for a proper whodunit.",
        {"coop", "straw", "farm"},
    ),
}

LOADS = {
    "feed_bag": Load("feed_bag", "feed bag", "the feed bag", "heavy", "the feed room", {"load", "feed"}),
    "toolbox": Load("toolbox", "toolbox", "the toolbox", "heavy", "the shed shelf", {"load", "tools"}),
    "market_bundle": Load("market_bundle", "market bundle", "the market bundle", "heavy", "the kitchen table", {"load", "market"}),
}

SUSPECTS = {
    "emu": Suspect("emu", "the emu", "had wandered off to peck at shiny things", True, True, {"emu", "feathers"}),
    "dog": Suspect("dog", "the dog", "was asleep by the gate", False, False, {"dog"}),
    "brother": Suspect("brother", "the brother", "had been fixing a fence and never left the yard", True, False, {"family"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Maya"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Max", "Eli", "Noah"]
TRAITS = ["careful", "curious", "patient", "smart"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for load in LOADS:
            for suspect in SUSPECTS:
                if load == "toolbox" and suspect == "dog":
                    continue
                combos.append((place, load, suspect))
    return combos


def explain_rejection(place: str, load: str, suspect: str) -> str:
    if load == "toolbox" and suspect == "dog":
        return "(No story: the dog cannot plausibly move the toolbox, so the mystery would not hold.)"
    return "(No story: this combination does not support a believable whodunit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld about a missing load and an emu.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--ending", choices=["bad", "good"], help="force a bad or good ending")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.load is None or c[1] == args.load)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.place and args.load and args.suspect and (args.place, args.load, args.suspect) not in valid_combos():
        raise StoryError(explain_rejection(args.place, args.load, args.suspect))
    place, load, suspect = rng.choice(sorted(combos))
    ending = args.ending or "bad"
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or _pick_name(rng, gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    return StoryParams(place, load, suspect, ending, name, gender, helper, helper_gender)


def _rule_spread(world: World) -> list[str]:
    out = []
    if world.facts.get("wrong_penalty") and not world.facts.get("real_clue_found"):
        key = ("sadness",)
        if key not in world.fired:
            world.fired.add(key)
            world.get("detective").memes["sadness"] += 1
            out.append("__sad__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    for rule in [_rule_spread]:
        sents = rule(world)
        produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(place: Place, load: Load, suspect: Suspect, ending: str,
         detective_name: str, detective_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World()
    detective = world.add(Entity("detective", "character", detective_gender, label="the detective", role="detective"))
    helper = world.add(Entity("helper", "character", helper_gender, label="the helper", role="helper"))
    target = world.add(Entity("load", "thing", "thing", label=load.label, role="mystery"))
    emu = world.add(Entity("emu", "character", "thing", label="the emu", role="suspect"))
    world.facts.update(place=place, load=load, suspect=suspect, ending=ending, detective=detective, helper=helper, target=target)

    detective.id = detective_name
    helper.id = helper_name

    detective.memes["curiosity"] += 1
    helper.memes["doubt"] += 1

    world.say(
        f"At {place.label}, {detective_name} found that {load.phrase} had gone missing. "
        f"The only fresh tracks led past a feather print and toward the emu pen."
    )
    world.say(
        f'"{helper_name}, this is a puzzler," {detective_name} said. '
        f'"Someone moved {load.label}, but who?"'
    )

    world.para()
    world.say(f"The clues were small but stubborn: {place.clue_spots[0]}, {place.clue_spots[1]}, and {place.clue_spots[2]}.")
    world.say(f"The emu looked guilty because {suspect.alibi}.")

    if suspect.id == "emu":
        world.say(f'{detective_name} decided the emu must have done it and whispered, "I will penal-ize the emu."')
        world.facts["wrong_penalty"] = True
        detective.memes["certainty"] += 1
        emu.memes["fear"] += 1
        world.say(
            f"{detective_name} put the blame on the emu without checking the shelf, and the emu was made to stand in the corner."
        )
        world.say(
            f"But the {load.label} was still missing, and the real clue stayed hidden under a board."
        )
        if ending == "bad":
            world.para()
            world.say(
                f"By nightfall the mistake had grown worse. A storm blew in, the gate blew open, and the load was lost for good."
            )
            world.say(
                f"{helper_name} found the emu shivering in the dark, and {detective_name} had to admit the answer had been wrong all along."
            )
            world.say(
                f"The case ended badly: the emu was punished, the real thief slipped away, and the barn stayed a mystery."
            )
        else:
            world.para()
            world.say(
                f"{helper_name} stopped {detective_name} and pointed to the hidden scratch marks under the board."
            )
            world.say(
                f"Together they found the real clue and brought back the {load.label}, then apologized to the emu."
            )
    else:
        world.say(
            f"{helper_name} noticed that {suspect.alibi}, so {detective_name} looked again instead of blaming too fast."
        )
        world.say(
            f"They followed the tiny marks to a hidden nook and found the {load.label} tucked away where no one first looked."
        )
        if ending == "bad":
            world.para()
            world.say(
                f"Still, the final guess was rushed. {detective_name} accused the wrong creature anyway, and the true answer stayed out of sight."
            )
            world.say(
                f"The case closed with a bad ending: the wrong one was penalized, and the missing load remained missing."
            )
        else:
            world.para()
            world.say(
                f"{detective_name} solved the case at last, and the {load.label} was carried home in the warm afternoon light."
            )
            world.say(f"The emu was left alone, pecking at straw, while the mystery finally made sense.")

    world.facts["real_clue_found"] = ending != "bad"
    propagate(world, narrate=False)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit story for a young child that includes the words "penal-ize", "load", and "emu".',
        f"Tell a mystery story where {f['detective'].id} sees a missing {f['load'].label} and suspects the emu, but the clues do not quite fit.",
        f"Write a bad-ending detective story in a farm setting where someone is blamed too quickly and the real answer is missed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    dq = f["detective"].id
    hq = f["helper"].id
    load = f["load"].label
    qa = [
        QAItem(
            question="What went missing in the story?",
            answer=f"The {load} went missing. That was the mystery {dq} had to solve."
        ),
        QAItem(
            question="Why did {0} think the emu was involved?".format(dq),
            answer=f"{dq} saw feather-like tracks and the clues led near the emu pen. That made the emu seem suspicious before anyone checked more carefully."
        ),
        QAItem(
            question="How did the bad ending happen?",
            answer=f"{dq} blamed and penalized the emu too quickly, but the real clue was still hidden. Because the wrong choice was made, the case ended badly and the missing load stayed lost."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an emu?",
            answer="An emu is a very tall bird that cannot fly. It can run fast and peck at things on the ground."
        ),
        QAItem(
            question="What does it mean to penalize someone?",
            answer="To penalize someone is to punish them for something. A fair penalty should be based on the real facts."
        ),
        QAItem(
            question="What is a load?",
            answer="A load is something carried or moved, often something heavy like a bag or a box."
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("barn", "feed_bag", "emu", "bad", "Mia", "girl", "Noah", "boy"),
    StoryParams("yard", "toolbox", "brother", "good", "Leo", "boy", "Ava", "girl"),
    StoryParams("coop", "market_bundle", "emu", "bad", "Nora", "girl", "Eli", "boy"),
]


ASP_RULES = r"""
valid(P, L, S) :- place(P), load(L), suspect(S).
bad_end(P, L, S) :- valid(P, L, S), suspect(S), S = emu.
good_end(P, L, S) :- valid(P, L, S), not bad_end(P, L, S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import inside ASP helper
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for lid in LOADS:
        lines.append(asp.fact("load", lid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("  only in ASP:", sorted(cl - py))
        print("  only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke-tested ordinary generation.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        LOADS[params.load],
        SUSPECTS[params.suspect],
        params.ending,
        params.detective_name,
        params.detective_gender,
        params.helper_name,
        params.helper_gender,
    )
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
