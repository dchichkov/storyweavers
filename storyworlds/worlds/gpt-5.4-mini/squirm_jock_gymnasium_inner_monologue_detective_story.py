#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/squirm_jock_gymnasium_inner_monologue_detective_story.py
========================================================================================

A standalone storyworld for a tiny detective tale set in a gymnasium.

Seed words:
- squirm
- jock
- gymnasium

Style:
- Detective Story

Feature:
- Inner Monologue

Premise:
A young detective searches a gymnasium for a missing trophy whistle. A boastful jock
acts suspicious, the detective's inner monologue spots the real clue, and the truth
turns out to be kinder than it first seemed: the jock was trying to hide a surprise
gift, not a theft.

This script follows the storyworld contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --seed, -n, --all, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasonableness checks and an inline ASP twin
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
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
class Setting:
    id: str
    label: str
    echo: str
    dark_spot: str

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
    boast: str
    tell: str
    truth: str
    suspicious: int = 0

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
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    hidden: bool = False

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
class Outcome:
    id: str
    sense: int
    text: str
    qa_text: str
    tag: str = ""

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


SETTINGS = {
    "gymnasium": Setting("gymnasium", "the gymnasium", "high echoes and squeaky shoes", "the far locker corner"),
    "locker_room": Setting("locker_room", "the locker room", "metal clanks and soft whispers", "the bench by the lockers"),
    "empty_court": Setting("empty_court", "the empty court", "bouncing footsteps and a whistle's memory", "the center circle"),
}

SUSPECTS = {
    "jock": Suspect(
        "jock", "a jock", "puffed out his chest",
        "kept tugging at his gym bag",
        "was trying to hide a surprise gift",
        suspicious=2,
    ),
    "captain": Suspect(
        "captain", "the team captain", "talked like a champ",
        "kept glancing at the scoreboard",
        "was protecting a practice plan",
        suspicious=1,
    ),
    "coach_helper": Suspect(
        "coach_helper", "a coach helper", "spoke in short, careful words",
        "was carrying a folded note",
        "was helping arrange a surprise party",
        suspicious=0,
    ),
}

CLUES = {
    "ribbon": Clue("ribbon", "a blue ribbon", "a little blue ribbon under the bench", "a surprise gift, not a theft", hidden=True),
    "whistle": Clue("whistle", "the whistle", "the whistle on a strap", "the coach wanted it back", hidden=False),
    "note": Clue("note", "a note", "a folded note in the gym bag", "the jock was planning a surprise", hidden=True),
}

OUTCOMES = {
    "calm": Outcome("calm", 3, "closed the case with a smile",
                    "closed the case with a smile and a clear answer"),
    "surprise": Outcome("surprise", 2, "unwrapped the mystery as a surprise for the coach",
                        "unwrapped the mystery and learned it was a surprise"),
    "warning": Outcome("warning", 1, "caught the truth before anyone got upset",
                       "caught the truth before the coach got upset"),
}


def sensible_outcomes() -> list[Outcome]:
    return [o for o in OUTCOMES.values() if o.sense >= SENSE_MIN]


def best_outcome() -> Outcome:
    return max(OUTCOMES.values(), key=lambda o: o.sense)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for sus in SUSPECTS.values():
                if sid == "gymnasium" and clue.id in {"ribbon", "note"} and sus.id == "jock":
                    combos.append((sid, sus.id, cid))
                if sid in {"locker_room", "empty_court"} and clue.id == "whistle":
                    combos.append((sid, sus.id, cid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    suspect: str
    clue: str
    outcome: str
    detective: str
    detective_gender: str
    partner: str
    partner_gender: str
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


GIRL_NAMES = ["Mina", "Luna", "Nina", "Iris", "Piper", "Zoe", "Maya", "June"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Max", "Finn", "Owen", "Leo", "Jack"]
TRAITS = ["sharp", "quiet", "brave", "patient", "careful"]


def _pick_name(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return name, gender


def reasonableness_gate(setting: Setting, suspect: Suspect, clue: Clue) -> bool:
    return setting.id == "gymnasium" and suspect.id == "jock" and clue.id in {"ribbon", "note"}


def explain_rejection(setting: Setting, suspect: Suspect, clue: Clue) -> str:
    return (
        f"(No story: in this tiny detective world, {suspect.label} only makes sense "
        f"in the gymnasium when the clue is a hidden surprise like {clue.label}.)"
    )


def _r_doubt(world: World) -> list[str]:
    out: list[str] = []
    det = world.get("detective")
    if det.memes["doubt"] >= THRESHOLD and ("doubt",) not in world.fired:
        world.fired.add(("doubt",))
        det.memes["focus"] += 1
        out.append("__inner__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    suspect = world.get("suspect")
    if clue.meters["found"] >= THRESHOLD and suspect.meters["fidget"] >= THRESHOLD:
        sig = ("reveal", clue.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        suspect.memes["nervous"] += 1
        out.append("__reveal__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("truth").meters["known"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        for eid in ("detective", "partner", "suspect"):
            world.get(eid).memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [_r_doubt, _r_reveal, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_truth(world: World) -> dict:
    sim = world.copy()
    sim.get("detective").memes["doubt"] += 1
    sim.get("clue").meters["found"] += 1
    sim.get("suspect").meters["fidget"] += 1
    propagate(sim, narrate=False)
    return {
        "reveal": sim.get("truth").meters["known"] >= THRESHOLD,
        "relief": sim.get("detective").memes["relief"],
    }


def tell(
    setting: Setting,
    suspect_cfg: Suspect,
    clue_cfg: Clue,
    outcome: Outcome,
    detective: str = "Mina",
    detective_gender: str = "girl",
    partner: str = "Eli",
    partner_gender: str = "boy",
) -> World:
    w = World()
    det = w.add(Entity(id="detective", kind="character", type=detective_gender, label=detective, role="detective"))
    part = w.add(Entity(id="partner", kind="character", type=partner_gender, label=partner, role="partner"))
    sus = w.add(Entity(id="suspect", kind="character", type="boy", label=suspect_cfg.label, role="suspect"))
    clue = w.add(Entity(id="clue", kind="thing", type="clue", label=clue_cfg.label))
    truth = w.add(Entity(id="truth", kind="thing", type="truth", label="the truth"))

    det.memes["doubt"] = 1
    det.memes["focus"] = 1
    sus.meters["fidget"] = 1

    w.say(
        f"At {setting.label}, {det.label} and {part.label} worked a small detective case. "
        f"The air had {setting.echo}, and {setting.dark_spot} looked like a place where secrets could hide."
    )
    w.say(
        f"{det.label} watched {suspect_cfg.label} and thought, "
        f'"My clue book says this could be a lie. But maybe it is only a tricky surprise."'
    )

    w.para()
    w.say(
        f"{sus.label} kept {suspect_cfg.boast}, while {suspect_cfg.tell}."
    )
    w.say(
        f'{det.label} squirmed a little inside the way detectives do when a case feels odd. '
        f'"What am I missing?" {det.label} wondered. "A jock can look guilty just by standing too tall."'
    )

    pred = predict_truth(w)
    if pred["reveal"]:
        w.say(
            f'{part.label} pointed to {clue_cfg.phrase}. {det.label} bent down and found it.'
        )
        clue.meters["found"] = 1
        sus.meters["fidget"] += 1
        w.say(
            f'"Aha," {det.label} whispered. "The clue is here because someone was hiding something, not stealing it."'
        )
    else:
        raise StoryError("This tiny detective story expects a clue that can actually be found.")

    w.para()
    clue.meters["found"] = 1
    truth.meters["known"] = 1
    w.say(
        f'{det.label} followed the clue, and the last piece clicked into place. '
        f'{sus.label.capitalize()} finally admitted {suspect_cfg.truth}.'
    )
    propagate(w, narrate=True)

    w.para()
    if outcome.id == "surprise":
        w.say(
            f'"So the jock was not a thief," {det.label} said with a grin. '
            f'"He was hiding a surprise gift in the gymnasium."'
        )
    elif outcome.id == "warning":
        w.say(
            f'"I caught it before anyone got upset," {det.label} said. '
            f'"The whole case was a surprise set for the coach."'
        )
    else:
        w.say(
            f'"Case closed," {det.label} said softly. '
            f'"The gymnasium had looked suspicious, but the truth was kind."'
        )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a young child that takes place in {f["setting"].label} and includes the word "squirm".',
        f'Tell a mystery story where {f["detective"]} solves the case in the gymnasium using an inner monologue and a clue tied to a jock.',
        f'Write a short detective tale with a suspicious jock, a gymnasium, and a surprise ending that feels safe and clear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    part = f["partner"]
    sus = f["suspect"]
    clue = f["clue"]
    setting = f["setting"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {det.label} and {part.label}, who tried to solve a mystery in {setting.label}. {det.label} also noticed the suspicious jock and kept thinking like a detective."
        ),
        QAItem(
            question=f"Why did {det.label} squirm inside?",
            answer=f"{det.label} squirmed because the case felt odd and the jock looked suspicious. {det.label} had to listen carefully to an inner monologue and follow the clue instead of jumping to the wrong answer."
        ),
        QAItem(
            question=f"What clue did they find?",
            answer=f"They found {clue_cfg_phrase(world)}. That clue mattered because it showed the jock was hiding a surprise, not causing trouble."
        ),
    ]
    if f["outcome"].id == "surprise":
        qa.append(
            QAItem(
                question="What was the jock really doing?",
                answer="The jock was hiding a surprise gift in the gymnasium. He looked guilty at first, but the clue showed he was trying to help, not steal."
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="The detective solved the mystery and learned the truth was kinder than it looked. The gymnasium became a place for a surprise instead of a worry."
            )
        )
    return qa


def clue_cfg_phrase(world: World) -> str:
    clue = world.facts["clue_cfg"]
    return clue.phrase


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gymnasium?",
            answer="A gymnasium is a big indoor room for sports, practice, and games. It usually has a hard floor, open space, and equipment like balls or hoops."
        ),
        QAItem(
            question="What does it mean to squirm?",
            answer="To squirm means to wiggle or move around in a worried or uncomfortable way. A person might squirm when they feel nervous or cannot sit still."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of a character's private thoughts. It lets the reader hear what the character is thinking without saying it out loud."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for oid, o in OUTCOMES.items():
        lines.append(asp.fact("outcome", oid))
        lines.append(asp.fact("sense", oid, o.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, J, C) :- setting(S), suspect(J), clue(C), S = "gymnasium", J = "jock", (C = "ribbon"; C = "note").
sensible(O) :- outcome(O), sense(O, N), sense_min(M), N >= M.
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
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    ok = 0
    if c == p:
        print(f"OK: gate matches valid_combos() ({len(c)} combos).")
    else:
        ok = 1
        print("MISMATCH in valid_combos():")
        print("  only in clingo:", sorted(c - p))
        print("  only in python:", sorted(p - c))
    c2, p2 = set(asp_sensible()), {o.id for o in sensible_outcomes()}
    if c2 == p2:
        print(f"OK: sensible outcomes match ({sorted(c2)}).")
    else:
        ok = 1
        print("MISMATCH in sensible outcomes.")
    return ok


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective storyworld set in a gymnasium.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--detective")
    ap.add_argument("--partner")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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
    if args.setting or args.suspect or args.clue:
        setting = SETTINGS[args.setting] if args.setting else SETTINGS["gymnasium"]
        suspect = SUSPECTS[args.suspect] if args.suspect else SUSPECTS["jock"]
        clue = CLUES[args.clue] if args.clue else CLUES["ribbon"]
        if not reasonableness_gate(setting, suspect, clue):
            raise StoryError(explain_rejection(setting, suspect, clue))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, suspect_id, clue_id = rng.choice(sorted(combos))
    outcome = args.outcome or rng.choice(sorted(o.id for o in sensible_outcomes()))
    det, det_g = (_pick_name(rng) if not args.detective else (args.detective, args.detective_gender or "girl"))
    part, part_g = (_pick_name(rng) if not args.partner else (args.partner, args.partner_gender or "boy"))
    return StoryParams(setting_id, suspect_id, clue_id, outcome, det, det_g, part, part_g)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], SUSPECTS[params.suspect], CLUES[params.clue],
        OUTCOMES[params.outcome], params.detective, params.detective_gender,
        params.partner, params.partner_gender,
    )
    world.facts.update(
        setting=SETTINGS[params.setting],
        suspect=SUSPECTS[params.suspect],
        clue_cfg=CLUES[params.clue],
        clue=world.get("clue"),
        outcome=OUTCOMES[params.outcome],
        detective=world.get("detective"),
        partner=world.get("partner"),
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


CURATED = [
    StoryParams("gymnasium", "jock", "ribbon", "surprise", "Mina", "girl", "Eli", "boy"),
    StoryParams("gymnasium", "jock", "note", "calm", "Noah", "boy", "Zoe", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible outcomes:", ", ".join(asp_sensible()))
        print()
        for item in asp_valid_combos():
            print(item)
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
