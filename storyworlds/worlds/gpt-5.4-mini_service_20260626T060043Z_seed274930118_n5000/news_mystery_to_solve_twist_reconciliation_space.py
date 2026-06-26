#!/usr/bin/env python3
"""
storyworlds/worlds/news_mystery_to_solve_twist_reconciliation_space.py
=======================================================================

A small space-adventure storyworld about news, a mystery to solve, a twist,
and a reconciliation.

Premise:
- A child on a ship or station hears news about a strange problem in space.
- They try to solve the mystery by following physical clues.
- A twist reveals the problem is not danger, but a misunderstood helper or
  signal.
- Reconciliation follows when the characters work together and the story ends
  with the news being shared calmly.

This world is intentionally small and constraint-checked:
- The mystery must be plausible for the chosen location.
- The twist must be compatible with the clue.
- The reconciliation must resolve the emotional conflict.

The prose is driven by simulated state rather than template swapping.
"""

from __future__ import annotations

import argparse
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    misread: str
    reveal: str
    place_need: set[str]
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    reveal_line: str
    cause: str
    fixes: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Reconciliation:
    id: str
    offer: str
    action: str
    ending: str
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


@dataclass
class StoryParams:
    setting: str
    mystery: str
    twist: str
    reconciliation: str
    name: str
    role: str
    partner: str
    seed: Optional[int] = None


SETTINGS = {
    "orbital_station": Setting(place="the orbital station", kind="station", affords={"signal", "crawl", "dock"}),
    "cargo_ship": Setting(place="the cargo ship", kind="ship", affords={"signal", "crawl", "dock"}),
    "moon_harbor": Setting(place="the moon harbor", kind="harbor", affords={"signal", "dock", "glow"}),
}

MYSTERIES = {
    "lost_news": Mystery(
        id="lost_news",
        label="missing news",
        clue="a blinking bulletin with one line cut off",
        misread="danger",
        reveal="the missing line was only a friendly update from a distant relay",
        place_need={"station", "ship", "harbor"},
        mess="static",
        risk="scary silence",
        tags={"news", "mystery", "signal"},
    ),
    "strange_light": Mystery(
        id="strange_light",
        label="strange light",
        clue="a silver blink in the window that seemed to follow the ship",
        misread="a spy drone",
        reveal="it was a rescue lamp from a dock worker waving at the hull",
        place_need={"station", "ship", "harbor"},
        mess="glow",
        risk="big worry",
        tags={"light", "mystery"},
    ),
    "mixed_message": Mystery(
        id="mixed_message",
        label="mixed message",
        clue="two news clips that did not fit together",
        misread="a mistake",
        reveal="the clips were from two rooms on the same ship, and both were true",
        place_need={"station", "ship"},
        mess="static",
        risk="mixed-up feelings",
        tags={"news", "message"},
    ),
}

TWISTS = {
    "helper_not_hurting": Twist(
        id="helper_not_hurting",
        label="hidden helper",
        reveal_line="the thing that looked wrong was actually helping",
        cause="the helper was changing the signal so the crew could hear it",
        fixes={"static", "glow"},
        tags={"twist", "helper"},
    ),
    "two_parts": Twist(
        id="two_parts",
        label="two-part truth",
        reveal_line="both clues belonged together",
        cause="one clue came from the speaker, and the other came from the listening room",
        fixes={"static"},
        tags={"twist", "truth"},
    ),
    "far_friend": Twist(
        id="far_friend",
        label="far-away friend",
        reveal_line="the surprise visitor was not a stranger at all",
        cause="a dock worker had sent the light to guide the ship safely in",
        fixes={"glow"},
        tags={"twist", "friend"},
    ),
}

RECONCILIATIONS = {
    "share_news": Reconciliation(
        id="share_news",
        offer="They could share the news together instead of guessing alone.",
        action="send a calm reply and read the bulletin out loud",
        ending="Soon the room felt warm again, because everyone knew the truth.",
        tags={"reconciliation", "news"},
    ),
    "say_sorry": Reconciliation(
        id="say_sorry",
        offer="They could say sorry for the hurried guess and start again.",
        action="slow down, listen carefully, and nod at each clue",
        ending="After that, the worry softened into relief.",
        tags={"reconciliation", "sorry"},
    ),
    "work_together": Reconciliation(
        id="work_together",
        offer="They could work together and let each person hold one clue.",
        action="split the clues, compare them, and smile when they matched",
        ending="By the end, the crew felt like one small team again.",
        tags={"reconciliation", "team"},
    ),
}

NAMES = ["Nova", "Milo", "Rin", "Ivy", "Kai", "Luna", "Tess", "Juno"]
ROLES = ["child", "cadet", "messenger", "helper"]
PARTNERS = ["captain", "pilot", "navigator", "friend"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for m_id, mystery in MYSTERIES.items():
            if setting.kind not in mystery.place_need:
                continue
            for t_id, twist in TWISTS.items():
                if not (twist.fixes & {mystery.mess, "news", "signal", "message", "static", "glow"}):
                    continue
                out.append((s_id, m_id, t_id))
    return out


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.label} does not fit {setting.place}. "
        f"The mystery needs a ship, station, or harbor where the clue can be seen and solved.)"
    )


def explain_twist_rejection(mystery: Mystery, twist: Twist) -> str:
    return (
        f"(No story: the twist '{twist.label}' does not help with {mystery.label}. "
        f"The twist must match the clue in a way the characters can notice and resolve.)"
    )


def activity_line(mystery: Mystery) -> str:
    return {
        "lost_news": "the blinking bulletin kept flickering like it wanted to say something important",
        "strange_light": "the silver blink kept sliding across the glass like a tiny moon",
        "mixed_message": "the two clips kept bumping into each other like mismatched puzzle pieces",
    }[mystery.id]


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    twist = TWISTS[params.twist]
    recon = RECONCILIATIONS[params.reconciliation]

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.role, label=params.name))
    partner = world.add(Entity(id="Partner", kind="character", type=params.partner, label=f"the {params.partner}"))
    clue = world.add(Entity(
        id="Clue",
        type="thing",
        label=mystery.label,
        phrase=mystery.clue,
        owner=partner.id,
    ))
    signal = world.add(Entity(
        id="Signal",
        type="thing",
        label="news bulletin",
        phrase="a small news bulletin with a blinking edge",
        owner=setting.kind,
    ))

    world.facts.update(hero=hero, partner=partner, clue=clue, signal=signal,
                       mystery=mystery, twist=twist, recon=recon, setting=setting)

    hero.memes["curiosity"] += 1
    partner.memes["worry"] += 1
    signal.meters["flicker"] += 1
    if mystery.id == "lost_news":
        clue.meters["static"] += 1
    elif mystery.id == "strange_light":
        clue.meters["glow"] += 1
    else:
        clue.meters["split"] += 1

    world.say(
        f"On {setting.place}, {hero.id} noticed {mystery.clue}. "
        f"It looked like {mystery.risk}, and {hero.id}'s curiosity rose fast."
    )
    world.say(
        f"At the same time, {partner.label} brought in a news bulletin, but one part of it seemed missing."
    )

    world.para()
    hero.memes["determination"] += 1
    world.say(
        f"{hero.id} wanted to solve the mystery, so {hero.pronoun()} checked the windows, the speaker, and the hatch."
    )
    if mystery.id == "lost_news":
        world.say("The bulletin crackled with static, so the message sounded broken.")
    elif mystery.id == "strange_light":
        world.say("The light kept flashing in the same place, so it felt like someone was signaling.")
    else:
        world.say("The two clips did not match, so the story felt split in half.")
    partner.memes["conflict"] += 1
    partner.meters["stress"] += 1
    world.say(
        f"{partner.label} worried the clue meant {mystery.misread}, and the room grew tense."
    )

    world.para()
    world.say(
        f"Then came the twist: {twist.reveal_line}. {twist.cause.capitalize()}."
    )
    world.say(
        f"That change fit the clue because it explained the {mystery.mess} without making the news false."
    )
    hero.memes["surprise"] += 1
    partner.memes["relief"] += 1

    world.para()
    world.say(recon.offer)
    world.say(
        f"So {hero.id} and {partner.label} chose to {recon.action}."
    )
    partner.memes["conflict"] = 0.0
    partner.memes["trust"] += 1
    hero.memes["joy"] += 1
    signal.meters["flicker"] = 0
    world.say(
        f"{recon.ending} The news was no longer scary; it was simply understood."
    )
    world.say(
        f"In the last light of the screen, {hero.id} and {partner.label} stood side by side, calm and reconciled."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    twist = f["twist"]
    recon = f["recon"]
    return [
        f'Write a short space-adventure story for a young child that includes the word "news" and a mystery to solve.',
        f"Tell a gentle story about {hero.id} on {world.setting.place} who notices {mystery.clue}, then discovers a twist and a reconciliation.",
        f"Write a tiny science-fiction story where news seems scary at first, but the truth is kinder than it looked.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    mystery = f["mystery"]
    twist = f["twist"]
    recon = f["recon"]
    return [
        QAItem(
            question=f"What did {hero.id} notice on {world.setting.place}?",
            answer=f"{hero.id} noticed {mystery.clue}. It seemed like a mystery because it looked like {mystery.risk}.",
        ),
        QAItem(
            question=f"Why did {partner.label} worry at first?",
            answer=f"{partner.label.capitalize()} worried because {mystery.misread} seemed likely until the clues were checked more carefully.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {twist.cause}, so the problem was not what it first seemed to be.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with reconciliation: {recon.ending}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is news?",
            answer="News is information about something that happened, something changed, or something people need to know.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or question that does not make sense right away, so people try to figure it out.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means calming a disagreement and helping people feel okay with each other again.",
        ),
        QAItem(
            question="Why do space crews use signals?",
            answer="Space crews use signals so ships and stations can send messages across a long distance where voices cannot travel easily.",
        ),
    ]
    if f["mystery"].id == "lost_news":
        out.append(QAItem(
            question="Why can static make a message hard to understand?",
            answer="Static adds crackly noise, so words can get cut off or sound fuzzy.",
        ))
    if f["mystery"].id == "strange_light":
        out.append(QAItem(
            question="What can a blinking light mean in space?",
            answer="A blinking light can be a signal, a warning, or a way to guide someone safely.",
        ))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbital_station", "lost_news", "helper_not_hurting", "share_news", "Nova", "child", "captain"),
    StoryParams("cargo_ship", "mixed_message", "two_parts", "work_together", "Milo", "cadet", "navigator"),
    StoryParams("moon_harbor", "strange_light", "far_friend", "say_sorry", "Ivy", "messenger", "pilot"),
]

ASP_RULES = r"""
mystery_place(M,S) :- setting(S), mystery(M), place_need(M,K), kind(S,K).
twist_fits(T,M) :- twist(T), mystery(M), fixes(T,F), mess(M,X), hit(F,X).
valid(S,M,T) :- mystery_place(M,S), twist_fits(T,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("kind", sid, s.kind))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("mess", mid, m.mess))
        for k in sorted(m.place_need):
            lines.append(asp.fact("place_need", mid, k))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        for fx in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, fx))
    for fx in {"static", "glow", "news", "signal", "message"}:
        lines.append(asp.fact("hit", fx, fx))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about news, mystery, twist, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--partner", choices=PARTNERS)
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
    if args.setting and args.mystery:
        s = SETTINGS[args.setting]
        m = MYSTERIES[args.mystery]
        if s.kind not in m.place_need:
            raise StoryError(explain_rejection(s, m))
    if args.mystery and args.twist:
        m = MYSTERIES[args.mystery]
        t = TWISTS[args.twist]
        if not (t.fixes & {m.mess, "news", "signal", "message", "static", "glow"}):
            raise StoryError(explain_twist_rejection(m, t))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, twist = rng.choice(sorted(combos))
    reconciliation = args.reconciliation or rng.choice(sorted(RECONCILIATIONS))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    partner = args.partner or rng.choice(PARTNERS)
    return StoryParams(setting=setting, mystery=mystery, twist=twist, reconciliation=reconciliation,
                       name=name, role=role, partner=partner)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combinations:")
        for combo in asp_valid_combos():
            print("  ", combo)
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
            header = f"### {p.name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
