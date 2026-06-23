#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/motive_twinkie_critic_airport_inner_monologue_dialogue.py
===============================================================================================================================

A standalone story world for a tiny airport superhero tale with inner monologue
and dialogue.

Seed premise:
- Airport setting
- Superhero-story style
- Required words: motive, twinkie, critic
- Features: inner monologue, dialogue

The world centers on a hero at an airport, a critical bystander, and a snack
(twinkie) that helps cool the moment while the hero remembers the true motive
for the trip.
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
    phrase: str = ""
    role: str = ""
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
        return self.label or self.type


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    critic = world.entities.get("critic")
    hero = world.entities.get("hero")
    if not critic or not hero:
        return out
    if hero.memes["confidence"] < THRESHOLD or hero.memes["resolve"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    critic.memes["doubt"] = max(0.0, critic.memes["doubt"] - 1.0)
    critic.memes["softened"] += 1
    out.append("The sharp edge in the crowd eased a little.")
    return out


CAUSAL_RULES = [Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class SettingCfg:
    id: str
    place: str
    detail: str


@dataclass
class Challenge:
    id: str
    problem: str
    inner_monologue: str
    dialogue_prompt: str
    turn: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "terminal": SettingCfg(id="terminal", place="the airport terminal", detail="The gate area hummed with rolling bags and bright screens."),
    "security": SettingCfg(id="security", place="the security line", detail="The line curled past bins and belt lights."),
    "gate": SettingCfg(id="gate", place="the gate", detail="The windows beside the gate showed a silver plane waiting outside."),
}

CHALLENGES = {
    "critic": Challenge(
        id="critic",
        problem="a critic with a sharp voice",
        inner_monologue="Maybe the critic is wrong, but the hero's motive still matters.",
        dialogue_prompt='\"You only wear that cape for attention,\" the critic said.',
        turn="The hero answered with a calm voice and remembered the real reason for the trip.",
        ending_image="The critic's frown softened, and the hero stood straighter under the airport lights.",
        tags={"critic", "dialogue", "monologue"},
    ),
    "delay": Challenge(
        id="delay",
        problem="a long delay and a tired crowd",
        inner_monologue="A delay could turn everybody snappish, so the hero needed patience as well as courage.",
        dialogue_prompt='\"This line is taking forever,\" someone muttered.',
        turn="The hero helped the line move and kept the mood steady.",
        ending_image="The screens still glowed, but the waiting people looked less restless.",
        tags={"delay", "dialogue", "monologue"},
    ),
    "lost_note": Challenge(
        id="lost_note",
        problem="a missing note with the destination address",
        inner_monologue="Without the note, the motive might get lost before the plane even left the ground.",
        dialogue_prompt='\"What are you looking for?\" asked the critic.',
        turn="The hero found the note tucked beside the twinkie and could explain the mission at last.",
        ending_image="The note was safe again in the hero's pocket, and the gate felt less chaotic.",
        tags={"note", "dialogue", "monologue"},
    ),
    "rumble": Challenge(
        id="rumble",
        problem="a rumbling stomach before the flight",
        inner_monologue="Even heroes need a small snack when the next step is far away.",
        dialogue_prompt='\"You really packed food for yourself?\" the critic said.',
        turn="The hero shared the twinkie and turned the complaint into a tiny truce.",
        ending_image="Crumbs were gone, and the hero's hands were steady around the boarding pass.",
        tags={"twinkie", "dialogue", "monologue"},
    ),
}

GIFTS = {
    "twinkie": Gift(
        id="twinkie",
        label="twinkie",
        phrase="a twinkie wrapped in bright paper",
        effect="a little sweetness can make a hard place feel kinder",
        tags={"twinkie", "snack"},
    ),
    "pass": Gift(
        id="pass",
        label="boarding pass",
        phrase="the boarding pass",
        effect="a kept promise can be stronger than doubt",
        tags={"pass"},
    ),
    "cape": Gift(
        id="cape",
        label="cape",
        phrase="a blue cape with a gold star",
        effect="a brave costume can remind the hero who they are",
        tags={"cape"},
    ),
    "note": Gift(
        id="note",
        label="note",
        phrase="a folded note",
        effect="a written reminder can keep a motive clear",
        tags={"note"},
    ),
}

HERO_NAMES = ["Nova", "Mina", "Rae", "Jules", "Ivy", "Piper", "Zuri", "Kai"]
SUPPORT_NAMES = ["Tess", "Milo", "Ben", "June", "Aria", "Nico", "Leah"]


@dataclass
class StoryParams:
    setting: str = "terminal"
    challenge: str = "critic"
    gift: str = "twinkie"
    hero_name: str = "Nova"
    hero_type: str = "girl"
    critic_name: str = "Tess"
    critic_type: str = "woman"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for c in CHALLENGES:
            for g in GIFTS:
                if c == "critic" or g == "twinkie" or c in {"rumble", "lost_note", "delay"}:
                    combos.append((s, c, g))
    return combos


def tell(setting: SettingCfg, challenge: Challenge, gift: Gift, hero_name: str, hero_type: str,
         critic_name: str, critic_type: str) -> World:
    world = World(setting=setting.id)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    critic = world.add(Entity(id="critic", kind="character", type=critic_type, label=critic_name, role="critic"))
    snack = world.add(Entity(id="snack", kind="thing", type="food", label=gift.label, phrase=gift.phrase))
    hero.memes["confidence"] = 1.0
    hero.memes["resolve"] = 0.0
    critic.memes["doubt"] = 1.0
    critic.memes["softened"] = 0.0
    world.facts.update(setting=setting, challenge=challenge, gift=gift, hero=hero, critic=critic, snack=snack)

    world.say(f"{hero.label} stood in {setting.place} wearing a cape that fluttered when the air conditioner sighed. {setting.detail}")
    world.say(f"Inside {hero.label}'s head, one thought kept glowing: the motive was bigger than the delay, the noise, or the critic.")

    world.para()
    world.say(f"{challenge.dialogue_prompt}")
    if challenge.id == "critic":
        world.say(f"\"The motive is simple,\" {hero.label} thought. \"I have to bring the {gift.label} and the note to the clinic before evening.\"")
        world.say(f"\"I am not here for applause,\" {hero.label} said. \"I'm here because someone is waiting.\"")
    elif challenge.id == "delay":
        world.say(f"\"I can keep this line moving,\" {hero.label} said, pointing people toward the right bins.")
        world.say(f"\"That helps,\" the critic admitted, and the hero's shoulders loosened.")
    elif challenge.id == "lost_note":
        world.say(f"\"Wait,\" {hero.label} thought, patting every pocket. \"The motive can't disappear with the paper.\"")
        world.say(f"\"I found it,\" {hero.label} said, lifting the folded note from beside the {gift.label}.")
    else:
        world.say(f"\"Would you like half?\" {hero.label} asked, holding up the twinkie.")
        world.say(f"\"Maybe I judged too fast,\" the critic said.")

    world.para()
    world.say(challenge.turn)
    hero.memes["resolve"] += 1.0
    propagate(world)
    if gift.id == "twinkie":
        hero.meters["sweet"] += 1.0
        critic.memes["doubt"] = max(0.0, critic.memes["doubt"] - 0.5)
        world.say("The twinkie was small, but it steadied the hero's hands and made the airport feel less stern.")
    elif gift.id == "note":
        hero.meters["order"] += 1.0
        world.say("The folded note stayed safe, and the motive stayed clear all the way to the gate.")
    elif gift.id == "cape":
        hero.memes["confidence"] += 1.0
        world.say("The cape caught a draft and reminded the hero to stand tall.")
    else:
        hero.meters["balance"] += 1.0
        world.say("The boarding pass was in the right pocket at last.")

    world.para()
    world.say(f"By the end, {challenge.ending_image}")
    if gift.id == "twinkie":
        world.say(f"The last crumb vanished, and {hero.label} still had the motive, the mission, and enough courage to board.")
    elif challenge.id == "critic":
        world.say(f"The critic even said, \"Okay. I see your motive now.\"")
    else:
        world.say(f"The airport lights shone on a hero who looked ready for the next flight.")

    world.facts.update(outcome="resolved")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story set in {f["setting"].place} that uses the words "motive", "twinkie", and "critic".',
        f'Write a short airport adventure where {f["hero"].label} keeps a true motive in mind while dealing with a critic and a twinkie.',
        f'Tell a child-friendly story with inner monologue and dialogue in an airport, ending with a hero proving the real motive.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    critic: Entity = f["critic"]
    setting: SettingCfg = f["setting"]
    challenge: Challenge = f["challenge"]
    gift: Gift = f["gift"]
    qa = [
        QAItem(
            question=f"Why was {hero.label} at {setting.place}?",
            answer=f"{hero.label} was there because {hero.pronoun('subject')} had a real motive for the trip. {hero.label} needed to keep going even when the airport felt noisy and slow.",
        ),
        QAItem(
            question=f"What did the critic say to {hero.label}?",
            answer=f"The critic said, \"You only wear that cape for attention,\" and tried to make the hero doubt the plan. That made the hero think harder about the true motive.",
        ),
        QAItem(
            question=f"How did the twinkie matter in the story?",
            answer=f"The twinkie gave the hero a small, steadying break. It also helped turn the critic's sharp mood into a calmer one.",
        ),
    ]
    if challenge.id == "critic":
        qa.append(QAItem(
            question=f"What did {hero.label} do after the critic complained?",
            answer=f"{hero.label} answered calmly and explained the motive without bragging. That made the critic soften and the story move toward a kinder ending.",
        ))
    if gift.id == "twinkie":
        qa.append(QAItem(
            question=f"Why was the twinkie a good snack for {hero.label}?",
            answer=f"It was small, sweet, and easy to carry at the airport. The hero could eat it quickly and keep moving toward the flight.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a motive?",
            answer="A motive is the reason someone does something. It is the thought or goal that pushes a person to act.",
        ),
        QAItem(
            question="What is a twinkie?",
            answer="A twinkie is a soft, sweet snack cake with cream inside. People often eat it as a treat.",
        ),
        QAItem(
            question="What is a critic?",
            answer="A critic is someone who notices problems and gives opinions. A critic can be helpful, but a sharp critic can also sound unkind.",
        ),
        QAItem(
            question="What happens in an airport?",
            answer="People go to an airport to catch planes, wait at gates, and carry bags through security. It is a busy place with signs, screens, and rolling suitcases.",
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
    lines.append("== (3) World knowledge ==")
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
    return "\n".join(lines)


ASP_RULES = r"""
good_combo(S,C,G) :- setting(S), challenge(C), gift(G).
said_critic :- challenge(critic).
twinkie_help :- gift(twinkie).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
        if g == "twinkie":
            lines.append(asp.fact("twinkie", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP combos")
        if cl - py:
            print(" only in ASP:", sorted(cl - py))
        if py - cl:
            print(" only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        _ = sample.to_json()
        print("OK: generation smoke test passed.")
    except Exception as err:
        ok = False
        print(f"SMOKE TEST FAILED: {err}")
    return 0 if ok else 1


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny airport superhero storyworld with motive, twinkie, and critic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--critic-name")
    ap.add_argument("--critic-type", choices=["woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, gift = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    critic_type = args.critic_type or rng.choice(["woman", "man"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    critic_name = args.critic_name or rng.choice([n for n in SUPPORT_NAMES if n != hero_name])
    return StoryParams(setting=setting, challenge=challenge, gift=gift, hero_name=hero_name, hero_type=hero_type, critic_name=critic_name, critic_type=critic_type)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.challenge not in CHALLENGES or params.gift not in GIFTS:
        raise StoryError("Invalid params")
    world = tell(SETTINGS[params.setting], CHALLENGES[params.challenge], GIFTS[params.gift],
                 params.hero_name, params.hero_type, params.critic_name, params.critic_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    StoryParams(setting="terminal", challenge="critic", gift="twinkie", hero_name="Nova", hero_type="girl", critic_name="Tess", critic_type="woman"),
    StoryParams(setting="gate", challenge="lost_note", gift="note", hero_name="Mina", hero_type="girl", critic_name="Ben", critic_type="man"),
    StoryParams(setting="security", challenge="delay", gift="cape", hero_name="Rae", hero_type="boy", critic_name="June", critic_type="woman"),
    StoryParams(setting="terminal", challenge="rumble", gift="twinkie", hero_name="Jules", hero_type="boy", critic_name="Nico", critic_type="man"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
