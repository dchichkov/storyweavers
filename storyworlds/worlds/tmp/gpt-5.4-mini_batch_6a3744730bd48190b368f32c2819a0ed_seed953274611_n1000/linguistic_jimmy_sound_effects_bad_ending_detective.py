#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/linguistic_jimmy_sound_effects_bad_ending_detective.py
======================================================================================

A small detective-style storyworld for a child-facing mystery about Jimmy,
linguistic clues, noisy sound effects, and a bad ending when the case goes
wrong.

Premise
-------
Jimmy is a little detective who loves words, sounds, and clues. He investigates
a tiny mystery in a room, a hall, or a yard. The world has two key tensions:

1) "linguistic" clues can help Jimmy solve the case if he notices words, labels,
   and meanings carefully.
2) "sound effects" can distract him or alarm others, and sometimes they lead to
   a bad ending if the wrong clue is followed.

The simulation keeps typed entities with physical meters and emotional memes.
A child-friendly story emerges from state changes, not from a fixed paragraph
with swapped nouns. The world can end in a safe solve, but the default / most
distinctive branch here is a bad ending where Jimmy chases the wrong clue and
the evidence gets lost.

This file follows the Storyweavers storyworld contract:
- StoryParams and registries
- build_parser / resolve_params / generate / emit / main
- Python validity gate plus inline ASP twin
- QA from world state, not by parsing rendered prose
- --verify includes a generation smoke test
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"scratched": 0.0, "lost": 0.0, "noise": 0.0}
        if not self.memes:
            self.memes = {"curious": 0.0, "fear": 0.0, "resolve": 0.0, "regret": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    shadow: str
    soundscape: str
    has_echo: bool = False


@dataclass
class CaseFile:
    id: str
    clue: str
    clue_word: str
    meaning: str
    sound: str
    lure: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    makes_noise: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Outcome:
    id: str
    sense: int
    ending: str
    fail: str
    success: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    setting: str
    casefile: str
    tool: str
    outcome: str
    jimmy: str
    jimmy_gender: str
    partner: str
    partner_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "office": Setting(id="office", place="the little office", shadow="long desk shadows",
                      soundscape="the hum of a lamp and the click of a clock", has_echo=True),
    "hall": Setting(id="hall", place="the hallway", shadow="thin shadows", soundscape="soft footsteps and a creaky floor"),
    "yard": Setting(id="yard", place="the back yard", shadow="tree shadows", soundscape="leaves rustling and a far gate"),
}

CASEFILES = {
    "note": CaseFile(
        id="note", clue="a note", clue_word="linguistic", meaning="words on paper",
        sound="scritch-scratch", lure="to read it out loud", risk="to miss the real clue",
        tags={"linguistic", "paper"},
    ),
    "label": CaseFile(
        id="label", clue="a label on a box", clue_word="linguistic", meaning="a word that names a thing",
        sound="tap-tap", lure="to test the labels", risk="to confuse the shelves",
        tags={"linguistic", "label"},
    ),
    "message": CaseFile(
        id="message", clue="a message on a card", clue_word="linguistic", meaning="words that tell what happened",
        sound="flip-flip", lure="to chase the message", risk="to lose the trail",
        tags={"linguistic", "message"},
    ),
}

TOOLS = {
    "jimmy": Tool(id="jimmy", label="Jimmy's little jimmy tool", use="to pry a stuck drawer", makes_noise=True, tags={"jimmy", "pry"}),
    "flash": Tool(id="flash", label="a flashlight", use="to shine on dark corners", makes_noise=False, tags={"light"}),
    "magnifier": Tool(id="magnifier", label="a magnifying glass", use="to inspect tiny marks", makes_noise=False, tags={"inspect"}),
}

OUTCOMES = {
    "solve": Outcome(id="solve", sense=3, ending="safe solve", fail="missed the point", success="noticed the clue and solved it", tags={"good"}),
    "spook": Outcome(id="spook", sense=2, ending="spooked solve", fail="got rattled but kept going", success="heard the noise and stayed calm", tags={"mixed"}),
    "bad": Outcome(id="bad", sense=1, ending="bad ending", fail="chased the wrong sound and lost the trail", success="almost solved it, but the clue slipped away", tags={"bad"}),
}

GIRLS = ["Mina", "Tess", "Luna", "Nora", "Ivy"]
BOYS = ["Jimmy", "Eli", "Theo", "Milo", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, case in CASEFILES.items():
            for tid in TOOLS:
                if case.clue_word == "linguistic" and tid in TOOLS:
                    combos.append((sid, cid, tid))
    return combos


def explain_bad_choice(params: StoryParams) -> str:
    if params.outcome == "bad" and params.tool == "flash":
        return "(No story: the flashlight is too sensible for the bad-ending branch. Pick the jimmy tool to let the clue go wrong.)"
    return "(No story: this combination does not make a clear detective mystery.)"


def _noise(world: World, who: Entity, amount: float, sound: str) -> None:
    who.meters["noise"] += amount
    world.say(sound)


def _lost_clue(world: World, clue: Entity, reason: str) -> None:
    clue.meters["lost"] += 1
    world.say(reason)


def _solve_or_fail(world: World, setting: Setting, case: CaseFile, tool: Tool, outcome: Outcome, jimmy: Entity, partner: Entity) -> None:
    world.say(f"At {setting.place}, {jimmy.id} and {partner.id} looked for clues under {setting.shadow}.")
    world.say(f"{jimmy.id} loved the {case.clue_word} clue because it was about {case.meaning}.")
    if tool.makes_noise:
        _noise(world, jimmy, 1.0, f"{tool.label.capitalize()} went clink-clink in the quiet room.")
    world.para()
    world.say(f"Then they found {case.clue}, with its {case.sound} sound written all over the trail.")
    if outcome.id == "bad":
        jimmy.memes["curious"] += 1
        jimmy.memes["fear"] += 1
        _noise(world, partner, 1.0, f"{partner.id} said, '{case.sound}!'")
        _lost_clue(world, world.get("evidence"), f"But {jimmy.id} listened to the sound effect instead of the word clue.")
        world.say(f"{jimmy.id} opened the wrong drawer with the jimmy tool, and the real note slid under the desk.")
        world.say(f"By the time they looked back, the message was gone and the case felt cold.")
        return
    jimmy.memes["resolve"] += 1
    world.say(f"{jimmy.id} used {tool.label} carefully and pointed at the exact word that mattered.")
    world.say(f"{partner.id} smiled, because the linguistic clue made the mystery clear.")
    world.say(f"In the end, {jimmy.id} solved it {outcome.success}, and the room felt calm again.")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    case = CASEFILES[params.casefile]
    tool = TOOLS[params.tool]
    outcome = OUTCOMES[params.outcome]

    jimmy = world.add(Entity(id=params.jimmy, kind="character", type=params.jimmy_gender, role="detective"))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_gender, role="helper"))
    evidence = world.add(Entity(id="evidence", kind="thing", type="note", label=case.clue, tags=case.tags))

    world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    world.facts.update(setting=setting, case=case, tool=tool, outcome=outcome, jimmy=jimmy, partner=partner, evidence=evidence)

    world.say(f"Jimmy was a little detective who liked words, clues, and the tiny music of a case.")
    world.say(f"One day, he and {partner.id} entered {setting.place}, where the air was full of {setting.soundscape}.")
    world.say(f"The mystery started with {case.clue}, and Jimmy said the word {case.clue_word} out loud like a key.")
    world.para()
    _solve_or_fail(world, setting, case, tool, outcome, jimmy, partner)
    if outcome.id == "bad":
        world.para()
        world.say("A rainy hush settled over the case, and the answer never came back.")
        world.say("Jimmy walked home with a scribble of clues and a bad feeling in his pocket.")
    else:
        world.para()
        world.say(f"After that, they put the file away, and {setting.place} felt bright and ordinary again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the word "linguistic" and the word "jimmy".',
        f"Tell a small mystery story where {f['jimmy'].id} notices a {f['case'].clue_word} clue, but a noisy tool makes the case harder.",
        f"Write a story with sound effects, a detective feel, and a bad ending where the wrong clue gets followed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    jimmy, partner, case, outcome = f["jimmy"], f["partner"], f["case"], f["outcome"]
    qa = [
        ("Who is the story about?", f"It is about {jimmy.id}, a little detective, and {partner.id}, who helps with the case."),
        ("What kind of clue did Jimmy notice?", f"He noticed a {case.clue_word} clue, which means a clue made of words and labels. That kind of clue can tell you what happened if you read it carefully."),
    ]
    if outcome.id == "bad":
        qa.append((
            "Why was the ending bad?",
            f"Jimmy chased the noisy clue instead of the real one, so the evidence got lost. The bad ending happens because the sound effect pulled him away from the words he needed."
        ))
    else:
        qa.append((
            "How did the case end?",
            f"Jimmy stayed calm and used the clue the right way, so the mystery was solved. The ending was safe because the word clue mattered more than the noise."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a detective do?", "A detective looks for clues and tries to figure out what happened."),
        ("What is a sound effect?", "A sound effect is a sound that helps a story feel lively, like clink-clink or tap-tap."),
        ("What does linguistic mean?", "Linguistic means about language, words, or how words are used."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} tags={sorted(e.tags)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASEFILES:
        lines.append(asp.fact("casefile", cid))
        lines.append(asp.fact("linguistic", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for oid, o in OUTCOMES.items():
        lines.append(asp.fact("outcome", oid))
        lines.append(asp.fact("sense", oid, o.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,T) :- setting(S), casefile(C), linguistic(C), tool(T).
bad_end(T) :- outcome(T), sense(T, S), S < 2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with linguistic clues and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--casefile", choices=CASEFILES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--jimmy")
    ap.add_argument("--jimmy-gender", choices=["boy", "girl"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["boy", "girl"])
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
    combos = valid_combos()
    setting, casefile, tool = args.setting, args.casefile, args.tool
    if args.outcome and args.outcome == "bad" and args.tool == "flash":
        raise StoryError(explain_bad_choice(StoryParams(setting or "office", casefile or "note", tool or "flash", "bad", "Jimmy", "boy", "Mina", "girl")))
    if setting and casefile and tool and (setting, casefile, tool) not in combos:
        raise StoryError("(No story: that combination does not work.)")
    picks = [c for c in combos if (not setting or c[0] == setting) and (not casefile or c[1] == casefile) and (not tool or c[2] == tool)]
    if not picks:
        raise StoryError("(No valid combination matches the given options.)")
    setting, casefile, tool = rng.choice(sorted(picks))
    outcome = args.outcome or rng.choice(sorted(OUTCOMES))
    jimmy_gender = args.jimmy_gender or "boy"
    partner_gender = args.partner_gender or rng.choice(["boy", "girl"])
    jimmy = args.jimmy or "Jimmy"
    partner = args.partner or rng.choice(GIRLS if partner_gender == "girl" else BOYS)
    if partner == jimmy:
        partner = "Mina" if jimmy != "Mina" else "Theo"
    return StoryParams(setting=setting, casefile=casefile, tool=tool, outcome=outcome,
                       jimmy=jimmy, jimmy_gender=jimmy_gender, partner=partner, partner_gender=partner_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.casefile not in CASEFILES or params.tool not in TOOLS or params.outcome not in OUTCOMES:
        raise StoryError("invalid params")
    world = tell(params)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="office", casefile="note", tool="jimmy", outcome="bad", jimmy="Jimmy", jimmy_gender="boy", partner="Mina", partner_gender="girl"),
    StoryParams(setting="hall", casefile="label", tool="magnifier", outcome="solve", jimmy="Jimmy", jimmy_gender="boy", partner="Theo", partner_gender="boy"),
    StoryParams(setting="yard", casefile="message", tool="flash", outcome="spook", jimmy="Jimmy", jimmy_gender="boy", partner="Ivy", partner_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        rc = asp_verify()
        try:
            sample = generate(CURATED[0])
            if not sample.story.strip():
                rc = 1
        except Exception:
            rc = 1
        sys.exit(rc)
    if args.asp:
        import asp
        model = asp.one_model(asp_program(show="#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
