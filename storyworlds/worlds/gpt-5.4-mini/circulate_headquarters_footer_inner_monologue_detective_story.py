#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/circulate_headquarters_footer_inner_monologue_detective_story.py
================================================================================================

A standalone story world for a tiny detective tale: a child detective at
headquarters notices a clue that keeps getting circulated, reads the footer of a
paper trail, and follows an inner monologue from suspicion to a calm reveal.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate
- an inline ASP twin for parity checks
- three QA sets grounded in the simulated world state

The seed words are woven in as part of the domain:
- circulate
- headquarters
- footer

Style target: detective story, but child-facing and concrete.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    location: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
    details: str
    noise: str
    calm_cover: str


@dataclass
class Clue:
    id: str
    phrase: str
    seen_as: str
    location: str
    kind: str
    circulates: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Footer:
    id: str
    label: str
    line: str
    hidden_hint: str
    readable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Answer:
    id: str
    skill: str
    action: str
    effect: str
    fail: str
    tags: set[str] = field(default_factory=set)


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


def _r_anxiety(world: World) -> list[str]:
    out: list[str] = []
    if world.get("detective").memes["worry"] < THRESHOLD:
        return out
    if ("anxiety",) in world.fired:
        return out
    world.fired.add(("anxiety",))
    world.get("detective").memes["focus"] += 1
    out.append("__inner__")
    return out


def _r_circulate(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["circulation"] < THRESHOLD:
        return out
    sig = ("circulate", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("headquarters").meters["busyness"] += 1
    world.get("detective").memes["suspicion"] += 1
    out.append(f"The clue kept circulating through headquarters, and every hand that touched it made the room feel busier.")
    return out


def _r_footer(world: World) -> list[str]:
    out: list[str] = []
    foot = world.get("footer")
    if foot.meters["read"] < THRESHOLD:
        return out
    sig = ("footer", foot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("detective").memes["certainty"] += 1
    out.append(f"The footer gave the last needed hint, small but plain, like a fingerprint at the edge of a page.")
    return out


def _r_resolution(world: World) -> list[str]:
    detective = world.get("detective")
    culprit = world.get("culprit")
    if detective.meters["case_closed"] < THRESHOLD:
        return []
    sig = ("resolution",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["shame"] += 1
    return ["__close__"]


CAUSAL_RULES = [Rule("anxiety", _r_anxiety), Rule("circulate", _r_circulate), Rule("footer", _r_footer), Rule("resolution", _r_resolution)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule.apply(world)
            if parts:
                changed = True
                produced.extend(p for p in parts if not p.startswith("__"))
    if narrate:
        for p in produced:
            world.say(p)
    return produced


def reasonableness_gate(clue: Clue, footer: Footer, answer: Answer) -> bool:
    return clue.circulates and footer.readable and answer.skill >= SENSE_MIN


def sensible_answers() -> list[Answer]:
    return [a for a in ANSWERS.values() if a.skill >= SENSE_MIN]


def case_strength(clue: Clue, delay: int) -> int:
    return clue.location.count("hall") + delay + (1 if clue.circulates else 0)


def can_close(answer: Answer, clue: Clue, delay: int) -> bool:
    return answer.skill >= case_strength(clue, delay)


def predict_close(world: World) -> dict:
    sim = world.copy()
    _do_case(sim, narrate=False)
    return {
        "closed": sim.get("detective").meters["case_closed"] >= THRESHOLD,
        "busyness": sim.get("headquarters").meters["busyness"],
    }


def _do_case(world: World, narrate: bool = True) -> None:
    detective = world.get("detective")
    clue = world.get("clue")
    footer = world.get("footer")
    detective.meters["case_closed"] += 1
    clue.meters["circulation"] += 1
    footer.meters["read"] += 1
    propagate(world, narrate=narrate)


def open_story(world: World, detective: Entity, helper: Entity, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At {setting.place}, the small detective kept a careful notebook and watched the office lights hum. "
        f"{setting.details}"
    )
    world.say(
        f'"If something is wrong," {detective.id} thought, "I can tell by the tiny signs first."'
    )


def clue_arrives(world: World, clue: Clue, setting: Setting) -> None:
    clue.meters["circulation"] += 1
    world.get("detective").memes["worry"] += 1
    world.say(
        f"A slip of paper had been passed around and around, until it reached {setting.place} looking worn and important. '
        f"The note said it should circulate quietly, but the detective did not trust quiet paper."
    )


def inspect_footer(world: World, footer: Footer) -> None:
    footer.meters["read"] += 1
    world.say(
        f'At the bottom of the page, the footer hid a neat little line: "{footer.line}". '
        f"The detective bent closer, because the last line often tells the truest part of a story."
    )


def inner_monologue(world: World, detective: Entity, clue: Clue, footer: Footer) -> None:
    detective.memes["worry"] += 1
    world.say(
        f'"Something does not fit," {detective.id} thought. '
        f'"The clue keeps trying to circulate, but the footer is where the answer sits. '
        f'If I follow the edge of the page, I may find who moved it."'
    )


def accuse(world: World, detective: Entity, culprit: Entity) -> None:
    detective.memes["resolve"] += 1
    world.say(
        f'{detective.id} looked up and said, "The paper was not lost. It was moved on purpose." '
        f"{culprit.id} froze under the lamp."
    )


def reveal(world: World, culprit: Entity, clue: Clue, footer: Footer) -> None:
    world.say(
        f'{culprit.id} gave a small nod and admitted the truth. '
        f'The missing note had been tucked behind the footer so nobody would notice the schedule change.'
    )
    world.say(
        f"The detective matched the footer line, the circulating copies, and the dates in the ledger. "
        f"At last the whole case fit together."
    )


def close_case(world: World, detective: Entity, helper: Entity, setting: Setting) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{detective.id} closed the notebook with a soft snap. "
        f"At headquarters, the buzzing room grew calm again, and the paper went where it belonged."
    )
    world.say(
        f"{helper.id} smiled and stacked the files in a tidy pile. "
        f"The last page showed the footer one more time, and this time it looked like a solved mystery."
    )


def tell(setting: Setting, clue: Clue, footer: Footer, answer: Answer,
         detective_name: str = "Mina", detective_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         culprit_name: str = "Mr. Gray", culprit_gender: str = "boy",
         delay: int = 0) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    culprit = world.add(Entity(id=culprit_name, kind="character", type=culprit_gender, role="culprit"))
    headquarters = world.add(Entity(id="headquarters", type="place", label="headquarters"))
    world.add(Entity(id="clue", type="thing", label=clue.seen_as, location=clue.location))
    world.add(Entity(id="footer", type="thing", label=footer.label))
    detective.memes["worry"] = 0.0
    helper.memes["calm"] = 0.0
    world.facts["delay"] = delay

    open_story(world, detective, helper, setting)
    world.para()
    clue_arrives(world, clue, setting)
    inspect_footer(world, footer)
    inner_monologue(world, detective, clue, footer)
    if not reasonableness_gate(clue, footer, answer):
        raise StoryError("This case does not support a believable detective turn.")

    if clue.circulates:
        world.get("clue").meters["circulation"] += 1

    if can_close(answer, clue, delay):
        world.para()
        accuse(world, detective, culprit)
        _do_case(world)
        reveal(world, culprit, clue, footer)
        close_case(world, detective, helper, setting)
        outcome = "closed"
    else:
        world.para()
        world.say(
            f"The detective tried a quick answer, but it was too small for the trail of copies and the busy room. "
            f"{setting.calm_cover} could not hide the missing detail, so the case stayed open."
        )
        culprit.memes["nervous"] += 1
        world.say(
            f"{helper.id} helped sort the papers anyway, and the detective promised to look again after lunch."
        )
        outcome = "open"

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        setting=setting,
        clue=clue,
        footer=footer,
        answer=answer,
        outcome=outcome,
        closed=(outcome == "closed"),
    )
    return world


SETTINGS = {
    "office": Setting("office", "headquarters", "The bulletin board was crowded with notes, and the desk lamp made a bright circle on the table.", "a soft printer hum", "the curtain by the window"),
    "station": Setting("station", "headquarters", "The evidence board leaned over a metal desk, and the hallway smelled faintly of paper and raincoats.", "boots on the floor", "the filing cabinet"),
    "attic_room": Setting("attic_room", "headquarters", "The attic office was narrow, with dust in the light and a shelf full of old case folders.", "the floorboards creaked", "the storage trunk"),
}

CLUES = {
    "memo": Clue("memo", "the memo", "a wrinkled memo", "the copy room", "paper", circulates=True, tags={"paper", "circulate"}),
    "page": Clue("page", "the page", "a torn page", "the hallway", "paper", circulates=True, tags={"paper", "circulate"}),
    "receipt": Clue("receipt", "the receipt", "a little receipt", "the file basket", "paper", circulates=True, tags={"paper", "circulate"}),
}

FOOTERS = {
    "date_footer": Footer("date_footer", "footer", "The date at the bottom did not match the day on the stamp.", "the date at the bottom", tags={"footer"}),
    "name_footer": Footer("name_footer", "footer", "The name in the footer matched the old delivery log.", "the name in the footer", tags={"footer"}),
    "note_footer": Footer("note_footer", "footer", "The tiny footer note said the file had been moved after lunch.", "the tiny footer note", tags={"footer"}),
}

ANSWERS = {
    "checklist": Answer("checklist", 3, "sort the timeline and compare stamps", "put the case in order", "was too hurried to see the pattern", tags={"solve"}),
    "search": Answer("search", 2, "look through the file drawer again", "find the missing page", "was not careful enough", tags={"search"}),
    "call": Answer("call", 1, "guess from the first clue only", "close the case too soon", "was too small to fit the whole trail", tags={"weak"}),
}

NAMES_G = ["Mina", "Ivy", "Nora", "Luna", "Zoe"]
NAMES_B = ["Ben", "Kai", "Leo", "Owen", "Theo"]
CAREFUL_TRAITS = ["careful", "patient", "steady", "observant"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for fid, footer in FOOTERS.items():
                for aid, ans in ANSWERS.items():
                    if reasonableness_gate(clue, footer, ans):
                        combos.append((sid, cid, fid))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    footer: str
    answer: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    culprit: str
    culprit_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "circulate": [("What does it mean for paper to circulate?", "If paper circulates, people pass it from hand to hand or send it around a place. It moves through a group instead of staying in one spot.")],
    "headquarters": [("What is headquarters?", "Headquarters is the main place where people gather, keep records, and organize the work. It is where the detective team starts and sorts things out.")],
    "footer": [("What is a footer on a page?", "A footer is the small bit of writing at the bottom of a page. It can hold a date, name, or other last clue.")],
    "paper": [("Why can papers be useful clues?", "Papers can show dates, names, and messages, so a detective can learn who handled them and when.")],
    "solve": [("What does a detective do to solve a case?", "A detective looks for clues, compares details, and checks what fits best until the mystery makes sense.")],
    "search": [("Why do detectives search again?", "They search again because one clue is often not enough. A second look can reveal what was missed the first time.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the words "{f["clue"].id}", "{f["setting"].place}", and "{f["footer"].label}".',
        f"Tell a mystery story where {f['detective'].id} thinks out loud, follows a clue that keeps circulating, and solves the problem by reading the footer.",
        f'Write a detective story with inner monologue about a paper trail at headquarters and a footer that reveals the answer.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det, helpr, culprit = f["detective"], f["helper"], f["culprit"]
    clue, footer, setting = f["clue"], f["footer"], f["setting"]
    qa = [
        ("Who is the story about?", f"It is about {det.id}, a small detective at {setting.place}, and {helpr.id}, who helped with the files."),
        ("What clue kept getting passed around?", f"{clue.seen_as} kept circulating through headquarters. That made the room busier and gave the detective a reason to look closer."),
        ("What did the footer do in the story?", f"The footer held the last useful hint. It showed the detective where to look when the first clue was not enough."),
        ("What was the detective thinking?", f'{det.id} was thinking, "Something does not fit. If I follow the edge of the page, I may find who moved it."'),
    ]
    if f["outcome"] == "closed":
        qa.append(("How did the detective solve the case?", f"{det.id} compared the circulating copies, the footer line, and the dates in the record. Then {culprit.id} admitted moving the note, and the case was closed."))
        qa.append(("How did the story end?", f"It ended with the mystery solved at headquarters. The papers were sorted, the room calmed down, and the final page made sense."))
    else:
        qa.append(("How did the story end?", f"The case stayed open because the first answer was too small for the whole trail. {det.id} and {helpr.id} kept working, so the mystery was not finished yet."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["clue"].tags) | set(world.facts["footer"].tags)
    if world.facts["outcome"] == "closed":
        tags |= set(world.facts["answer"].tags)
    out: list[tuple[str, str]] = []
    for key in ["circulate", "headquarters", "footer", "paper", "solve", "search"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if e.location:
            bits.append(f"location={e.location}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:11} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("office", "memo", "date_footer", "checklist", "Mina", "girl", "Ben", "boy", "Mr. Gray", "boy", "careful", 0),
    StoryParams("station", "page", "name_footer", "search", "Ivy", "girl", "Theo", "boy", "Ms. Reed", "girl", "observant", 1),
    StoryParams("attic_room", "receipt", "note_footer", "checklist", "Kai", "boy", "Luna", "girl", "Mr. Gray", "boy", "steady", 0),
]


def explain_rejection(clue: Clue, footer: Footer, answer: Answer) -> str:
    return (
        f"(No story: this combination is not believable for a detective turn. "
        f"The clue must circulate, the footer must be readable, and the answer "
        f"must be strong enough to close the case.)"
    )


def outcome_of(params: StoryParams) -> str:
    clue = CLUES[params.clue]
    footer = FOOTERS[params.footer]
    answer = ANSWERS[params.answer]
    return "closed" if can_close(answer, clue, params.delay) else "open"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.circulates:
            lines.append(asp.fact("circulates", cid))
    for fid, f in FOOTERS.items():
        lines.append(asp.fact("footer", fid))
        if f.readable:
            lines.append(asp.fact("readable", fid))
    for aid, a in ANSWERS.items():
        lines.append(asp.fact("answer", aid))
        lines.append(asp.fact("skill", aid, a.skill))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,F) :- setting(S), clue(C), footer(F), circulates(C), readable(F).
sensible(A) :- answer(A), skill(A, K), sense_min(M), K >= M.
closed(A,C,D) :- sensible(A), clue(C), delay(D), skill(A, K), strength(C, D, N), K >= N.
strength(C,D,N) :- circulates(C), delay(D), N = D + 2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show closed/1."))
    return "closed" if asp.atoms(model, "closed") else "open"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {a.id for a in sensible_answers()}:
        rc = 1
        print("MISMATCH in sensible answers")
    tests = list(CURATED)
    for s in range(20):
        try:
            tests.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            pass
    if any(asp_outcome(p) != outcome_of(p) for p in tests):
        rc = 1
        print("MISMATCH in outcomes")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    if rc == 0:
        print("OK: ASP/Python parity and story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with circulating clues and an inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--footer", choices=FOOTERS)
    ap.add_argument("--answer", choices=ANSWERS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--culprit")
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
    if args.clue and args.footer and args.answer:
        clue = CLUES[args.clue]
        footer = FOOTERS[args.footer]
        answer = ANSWERS[args.answer]
        if not reasonableness_gate(clue, footer, answer):
            raise StoryError(explain_rejection(clue, footer, answer))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.footer is None or c[2] == args.footer)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, footer = rng.choice(sorted(combos))
    answer = args.answer or rng.choice(sorted(a.id for a in sensible_answers()))
    detective_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    culprit_gender = rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(NAMES_G if detective_gender == "girl" else NAMES_B)
    helper = args.helper or rng.choice(NAMES_B if helper_gender == "boy" else NAMES_G)
    culprit = args.culprit or rng.choice(["Mr. Gray", "Ms. Reed", "Mrs. Vale"])
    trait = rng.choice(CAREFUL_TRAITS)
    delay = rng.randint(0, 1)
    return StoryParams(setting, clue, footer, answer, detective, detective_gender, helper, helper_gender, culprit, culprit_gender, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], FOOTERS[params.footer], ANSWERS[params.answer],
                 params.detective, params.detective_gender, params.helper, params.helper_gender,
                 params.culprit, params.culprit_gender, params.delay)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, c, f in combos:
            print(f"  {s:12} {c:10} {f}")
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
            header = f"### {p.detective} at {p.setting} ({p.clue}, {p.footer}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
