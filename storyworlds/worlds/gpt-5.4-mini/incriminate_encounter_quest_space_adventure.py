#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/incriminate_encounter_quest_space_adventure.py
===============================================================================

A standalone story world for a tiny Space Adventure quest where a crew faces an
unexpected encounter, a false clue might incriminate someone, and the truth is
revealed through careful observation rather than blame.

The domain keeps to a child-facing, classical shape:
- a small crew on a quest
- an encounter with a strange space visitor or object
- a risky accusation based on a misleading clue
- a calm turn where the crew tests the clue in the world
- a resolution proving who did what and what changed

The story engine uses typed entities with physical meters and emotional memes,
a tiny forward-chaining rule system, a reasonableness gate, an inline ASP twin,
and three Q&A sets grounded in the simulated world state.
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
    can_incriminate: bool = False
    can_quest: bool = False
    encounter: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class QuestFrame:
    id: str
    place: str
    goal: str
    light: str
    encounter_phrase: str
    ending_image: str

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
class Clue:
    id: str
    label: str
    source: str
    can_incriminate: bool = False
    truth: str = ""

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
class Encounter:
    id: str
    label: str
    kind: str
    harmless: bool = False
    trail: str = ""

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
class Verdict:
    id: str
    sense: int
    text: str
    reveal: str

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["doubt"] < THRESHOLD:
            continue
        sig = ("confusion", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("confusion", "social", _r_confusion)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)


def reasonableness_gate(clue: Clue, encounter: Encounter) -> bool:
    return clue.can_incriminate and encounter.kind in {"ghost", "robot", "beacon", "drone"}


def likely_truth(clue: Clue, encounter: Encounter) -> bool:
    return clue.truth == encounter.trail


def sensible_verdicts() -> list[Verdict]:
    return [v for v in VERDICTS.values() if v.sense >= 2]


def build_scene() -> None:
    pass


def tell(frame: QuestFrame, hero: Entity, mate: Entity, guide: Entity,
         clue: Clue, encounter: Encounter, verdict: Verdict) -> World:
    world = World()
    hero = world.add(copy.deepcopy(hero))
    mate = world.add(copy.deepcopy(mate))
    guide = world.add(copy.deepcopy(guide))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.label, can_incriminate=clue.can_incriminate))
    enc_ent = world.add(Entity(id="encounter", type="thing", label=encounter.label, encounter=True))
    world.facts["frame"] = frame
    world.facts["hero"] = hero
    world.facts["mate"] = mate
    world.facts["guide"] = guide
    world.facts["clue"] = clue
    world.facts["encounter"] = encounter
    world.facts["verdict"] = verdict
    world.facts["clue_ent"] = clue_ent
    world.facts["enc_ent"] = enc_ent

    hero.memes["hope"] += 1
    mate.memes["hope"] += 1
    guide.memes["calm"] += 1

    world.say(
        f"On a quiet stretch of space, {hero.id} and {mate.id} drifted across "
        f"{frame.place} on a quest for {frame.goal}. {frame.light}"
    )
    world.say(
        f"Then came a strange {encounter.kind} encounter. {frame.encounter_phrase}"
    )

    world.para()
    if clue.can_incriminate:
        hero.memes["doubt"] += 1
        world.say(
            f"{hero.id} spotted {clue.label} and gasped, because it could "
            f"incriminate someone at first glance."
        )
        world.say(f'"Maybe {clue.source} did it," {hero.id} whispered.')
        if likely_truth(clue, encounter):
            world.say(
                f"But {guide.id} knelt beside the clue and looked at the trail "
                f"it really matched. The clue belonged to {encounter.label}, not "
                f"to a friend."
            )
            world.say(
                f'"Let the scene speak," {guide.id} said. "{verdict.text}"'
            )
            encounter_score = 1
        else:
            world.say(
                f"But {guide.id} shook {guide.pronoun("possessive")} head. "
                f"The clue was too easy to blame, and the trail did not fit."
            )
            world.say(
                f'"We should not incriminate anyone before checking the track," '
                f'{guide.id} said.'
            )
            encounter_score = 0
    else:
        world.say(
            f"{guide.id} pointed out that the clue was harmless, so nobody had "
            f"to blame anyone. They kept moving carefully."
        )
        encounter_score = 0

    world.para()
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    if encounter.harmless:
        world.say(
            f"At last, the crew found the hidden {frame.goal} and used it to "
            f"complete the quest."
        )
    else:
        world.say(
            f"They followed the true trail past the encounter and found the "
            f"hidden map crystal at the end of the quest."
        )
    world.say(frame.ending_image)
    world.facts["encounter_score"] = encounter_score
    return world


THEMES = {
    "space": QuestFrame(
        "space",
        "the silent moon corridor",
        "the lost star map",
        "Their helmet lights blinked like tiny stars.",
        "A glowing dust-cloud drifted across the tunnel, and one shiny print was left behind.",
        "The shuttle window showed the crew floating home, with the honest clue tucked safely in a pocket.",
    )
}

CLUES = {
    "glitter_print": Clue("glitter_print", "a glittery print", "the moon bot", True, "glitter"),
    "tool_mark": Clue("tool_mark", "a tool mark", "the repair drone", True, "metal"),
    "crumb_trail": Clue("crumb_trail", "a crumb trail", "the snack pack", True, "crumb"),
}

ENCOUNTERS = {
    "drone": Encounter("drone", "a repair drone", "drone", harmless=True, trail="metal"),
    "beacon": Encounter("beacon", "a blinking beacon", "beacon", harmless=True, trail="glitter"),
    "ghost": Encounter("ghost", "a dusty moon ghost", "ghost", harmless=True, trail="glitter"),
}

VERDICTS = {
    "check": Verdict("check", 3, "they checked the track and learned the clue was real", "check"),
    "wait": Verdict("wait", 2, "they waited and asked the guide before blaming anyone", "wait"),
    "rush": Verdict("rush", 1, "they rushed to accuse, but the guide stopped them", "rush"),
}

HEROES = ["Nova", "Milo", "Rin", "Tess", "Kai", "Luna"]
MATES = ["Pip", "Juno", "Bea", "Sol", "Pico", "Zed"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid in THEMES:
        for cid, clue in CLUES.items():
            for eid, enc in ENCOUNTERS.items():
                if reasonableness_gate(clue, enc):
                    combos.append((tid, cid, eid))
    return combos


@dataclass
@dataclass
class StoryParams:
    theme: str
    clue: str
    encounter: str
    hero: str
    mate: str
    guide: str
    verdict: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure quest with a clue that may incriminate.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--encounter", choices=ENCOUNTERS)
    ap.add_argument("--verdict", choices=VERDICTS)
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--guide", choices=["captain", "guide"])
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
    if args.clue and args.encounter:
        if not reasonableness_gate(CLUES[args.clue], ENCOUNTERS[args.encounter]):
            raise StoryError("No story: that clue cannot plausibly incriminate that encounter.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.clue is None or c[1] == args.clue)
              and (args.encounter is None or c[2] == args.encounter)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, clue, encounter = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HEROES)
    mate = args.mate or rng.choice([n for n in MATES if n != hero])
    guide = args.guide or "guide"
    verdict = args.verdict or rng.choice(sorted(sensible_verdicts(), key=lambda v: v.id)).id
    return StoryParams(theme, clue, encounter, hero, mate, guide, verdict)


def generate(params: StoryParams) -> StorySample:
    hero = Entity(id=params.hero, kind="character", type="girl" if params.hero in {"Nova", "Tess", "Luna"} else "boy", role="hero")
    mate = Entity(id=params.mate, kind="character", type="girl" if params.mate in {"Bea", "Juno"} else "boy", role="mate")
    guide = Entity(id="Guide", kind="character", type="captain", role="guide")
    world = tell(THEMES[params.theme], hero, mate, guide, CLUES[params.clue], ENCOUNTERS[params.encounter], VERDICTS[params.verdict])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure quest story that includes the words "incriminate" and "encounter".',
        f"Tell a child-friendly quest story where {f['hero'].id} sees a clue that could incriminate someone during an encounter in space, but the crew checks the evidence first.",
        f"Write a small space adventure where a guide helps two kids avoid blaming the wrong friend during a mysterious encounter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    guide = f["guide"]
    clue: Clue = f["clue"]
    encounter: Encounter = f["encounter"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, {mate.id}, and {guide.id} on a quest across space."),
        ("Why did the clue seem scary at first?",
         f"It seemed scary because it could incriminate someone at first glance. The crew did not want to blame the wrong traveler."),
        ("What helped them tell the truth?",
         f"{guide.id} looked at the trail and checked what the clue really matched. That careful step showed whether the clue belonged to the encounter or to someone else."),
        ("What did they learn at the end?",
         f"They learned that the clue could be tested against the scene before anyone was blamed. The quest moved forward because they chose evidence over guessing."),
    ]
    if clue.truth:
        qa.append((
            "What did the clue really match?",
            f"It matched the {clue.truth} trail, so it pointed to {encounter.label}. "
            f"That meant the clue was part of the encounter, not a reason to incriminate a friend."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an encounter?",
         "An encounter is a meeting with someone or something new, surprising, or strange."),
        ("What does it mean to incriminate someone?",
         "To incriminate someone means to make them look guilty. You should check the facts before you blame anybody."),
        ("What is a quest?",
         "A quest is a mission or journey to find something important or solve a problem."),
        ("What is a guide?",
         "A guide helps the group choose the right path and stay calm when things are confusing."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.can_incriminate:
            bits.append("can_incriminate=True")
        if e.encounter:
            bits.append("encounter=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
can_incriminate(C) :- clue(C), incriminate(C).
compatible(C, E) :- can_incriminate(C), encounter(E), trail(C, T), trail_of(E, T).
valid_story(T, C, E) :- theme(T), compatible(C, E).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy inside ASP helpers
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.can_incriminate:
            lines.append(asp.fact("incriminate", cid))
        if c.truth:
            lines.append(asp.fact("trail", cid, c.truth))
    for eid, e in ENCOUNTERS.items():
        lines.append(asp.fact("encounter", eid))
        lines.append(asp.fact("trail_of", eid, e.trail))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    try:
        clingo_set = set(asp_valid_combos())
        python_set = set(valid_combos())
        if clingo_set == python_set:
            print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
        else:
            rc = 1
            print("MISMATCH in the gate:")
            if clingo_set - python_set:
                print("  only in clingo:", sorted(clingo_set - python_set))
            if python_set - clingo_set:
                print("  only in python:", sorted(python_set - clingo_set))
        sample = generate(resolve_params(argparse.Namespace(theme=None, clue=None, encounter=None, verdict=None, name=None, mate=None, guide=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
        if "incriminate" not in sample.prompts[0]:
            raise RuntimeError("prompt missing seed word")
        print("OK: QA/prompts smoke test passed.")
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    return rc


def explain_rejection(clue: Clue, encounter: Encounter) -> str:
    return f"(No story: {clue.label} does not plausibly incriminate {encounter.label}.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (theme, clue, encounter) combos:")
        for t, c, e in asp_valid_combos():
            print(f"  {t:8} {c:14} {e}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("space", "glitter_print", "beacon", "Nova", "Pip", "Guide", "check"),
            StoryParams("space", "tool_mark", "drone", "Luna", "Sol", "Guide", "wait"),
            StoryParams("space", "crumb_trail", "ghost", "Milo", "Bea", "Guide", "check"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if i:
            print("\n" + "=" * 70 + "\n")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))


if __name__ == "__main__":
    main()
