#!/usr/bin/env python3
"""
storyworlds/worlds/silly_revert_kindness_misunderstanding_bravery_rhyming_story.py
====================================================================================

A small rhyming storyworld about a silly misunderstanding that gets turned back
with kindness and bravery.

Premise:
- A child notices something odd and gets the wrong idea.
- A friend or helper feels worried or embarrassed.
- A brave, kind action reveals the truth and reverts the misunderstanding.
- The ending lands on a warm, rhyming image showing what changed.

The world model tracks:
- physical meters: lost, held, wet, clean, swapped, tucked
- emotional memes: kindness, misunderstanding, bravery, worry, relief, joy

This script follows the Storyweavers contract:
- standalone stdlib script
- eager results import
- lazy asp import inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and exercises generated stories
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mishap: str
    reveal: str
    mess: str
    tag: str
    keyword: str


@dataclass
class Token:
    label: str
    phrase: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    setting: str
    activity: str
    token: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def rhyme_end(activity: Activity) -> str:
    return {
        "peek": "with a squeak and a peek",
        "message": "with a note that was bright and neat",
        "gift": "with a bow and a glow",
        "lantern": "with a light that danced just right",
    }.get(activity.id, "with a soft little rhyme")


def setting_line(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the floor was calm and neat."
    return f"At {setting.place}, the breeze was sweet."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.memes["worry"] += 1
    actor.meters[activity.mess] += 1
    if narrate:
        world.say(f"{actor.id} went to {activity.verb}, and the day began to lean.")


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["misunderstanding"] < THRESHOLD:
            continue
        sig = ("misunderstanding", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append(f"{actor.id} felt mixed-up and small.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"{actor.id} chose a kind step.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["bravery"] < THRESHOLD:
            continue
        sig = ("bravery", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"{actor.id} stood brave and bright.")
    return out


CAUSAL_RULES = [
    _r_misunderstanding,
    _r_kindness,
    _r_bravery,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story_world(setting: Setting, activity: Activity, token: Token,
                      name: str, gender: str, helper: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    friend = world.add(Entity(id=helper, kind="character", type="friend", label=helper))
    item = world.add(Entity(
        id="token", type=token.type, label=token.label, phrase=token.phrase,
        owner=hero.id, caretaker=friend.id, plural=token.plural
    ))

    world.facts.update(hero=hero, friend=friend, item=item, activity=activity, token=token)

    world.say(f"{hero.id} was a little {trait} {gender} with a heart for play.")
    world.say(f"{hero.id} loved {activity.gerund}, and {rhyme_end(activity)}.")

    world.para()
    world.say(setting_line(setting, activity))
    world.say(f"One day, {hero.id} saw {friend.id} near the {token.label}.")
    world.say(f"It looked odd, and {hero.id} got a silly thought in the head.")
    hero.memes["misunderstanding"] += 1
    propagate(world)

    world.para()
    world.say(f"{hero.id} wanted to know the truth, but {hero.pronoun()} did not want to tread.")
    hero.memes["bravery"] += 1
    world.say(f"So {hero.pronoun().capitalize()} took a brave breath and went to ask instead.")
    world.say(f"That kind question let {friend.id} explain what really had been said.")
    friend.memes["kindness"] += 1

    if activity.id == "peek":
        world.say(f"It was only a game of peek, and the hidden thing was never dead.")
    elif activity.id == "message":
        world.say(f"It was a tiny note, not a mean joke, and the mix-up slipped away.")
    elif activity.id == "gift":
        world.say(f"It was a surprise gift being wrapped, not a thing to put away.")
    else:
        world.say(f"It was just a lantern waiting there, not a sign of gloom or dread.")

    world.say("The silly misunderstanding began to revert.")
    hero.memes["misunderstanding"] = 0
    friend.memes["misunderstanding"] = 0

    world.para()
    world.say(f"{hero.id} smiled wide, and {friend.id} smiled too.")
    world.say(f"Their kindness made the worry thin, and bravery helped the truth shine through.")
    world.say(f"By the end, the air felt light, and the night felt new.")
    world.say(f"They stayed together, warm and calm, with a rhyming little view.")

    return world


SETTINGS = {
    "playroom": Setting(place="the playroom", indoor=True, affords={"peek", "message", "gift"}),
    "garden": Setting(place="the garden", indoor=False, affords={"peek", "message", "lantern"}),
    "porch": Setting(place="the porch", indoor=False, affords={"peek", "gift", "lantern"}),
}

ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="play a peek game",
        gerund="playing peek-a-boo",
        mishap="looked-hidden",
        reveal="a game was happening",
        mess="seen",
        tag="peek",
        keyword="peek",
    ),
    "message": Activity(
        id="message",
        verb="share a message",
        gerund="sharing messages",
        mishap="looked-secret",
        reveal="it was a note",
        mess="held",
        tag="note",
        keyword="message",
    ),
    "gift": Activity(
        id="gift",
        verb="wrap a gift",
        gerund="wrapping gifts",
        mishap="looked-hidden",
        reveal="it was a surprise",
        mess="tucked",
        tag="gift",
        keyword="gift",
    ),
    "lantern": Activity(
        id="lantern",
        verb="light a lantern",
        gerund="lighting lanterns",
        mishap="looked-far",
        reveal="it was only a lantern",
        mess="lit",
        tag="light",
        keyword="lantern",
    ),
}

TOKENS = {
    "box": Token(label="box", phrase="a small blue box", type="box"),
    "note": Token(label="note", phrase="a folded note", type="note"),
    "bundle": Token(label="bundle", phrase="a ribbon bundle", type="bundle", plural=False),
    "lamp": Token(label="lamp", phrase="a little lamp", type="lamp"),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ruby", "Zoe", "Ivy"]
BOY_NAMES = ["Leo", "Ben", "Max", "Finn", "Theo", "Sam"]
TRAITS = ["cheery", "curious", "squishy", "bright", "gentle", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        for act_id in setting.affords:
            for tok_id, tok in TOKENS.items():
                combos.append((sname, act_id, tok_id))
    return combos


def explain_rejection() -> str:
    return "(No story: that combination does not support a clear silly misunderstanding that can be turned back with kindness and bravery.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act, tok = f["hero"], f["friend"], f["activity"], f["token"]
    return [
        f"Write a short rhyming story for a child about {hero.id}, {friend.id}, and a silly misunderstanding.",
        f"Tell a gentle rhyme where {hero.id} thinks the {tok.label} means trouble, but kindness and bravery reveal the truth.",
        f"Write a small story that uses the word '{act.keyword}' and ends with the misunderstanding going away.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, act, tok = f["hero"], f["friend"], f["activity"], f["token"]
    return [
        QAItem(
            question=f"Who got the silly misunderstanding in the {world.setting.place} story?",
            answer=f"{hero.id} did, when {hero.pronoun()} saw {friend.id} near the {tok.label} and got the wrong idea.",
        ),
        QAItem(
            question=f"What helped the wrong idea revert in the end?",
            answer=f"Kindness and bravery helped the misunderstanding revert, because {hero.id} asked gently and {friend.id} told the truth.",
        ),
        QAItem(
            question=f"What was the child doing before the mix-up started?",
            answer=f"{hero.id} was {act.gerund}, and the story kept a soft rhyming beat while the day went on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing a gentle, helpful action that makes someone else feel safe and cared for.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone gets the wrong idea about what is happening.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel nervous or unsure.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(E) :- meme(E, misunderstanding), hero(E).
kind(E) :- meme(E, kindness), hero(E).
brave(E) :- meme(E, bravery), hero(E).

revert(E) :- hero(E), misunderstanding(E), kind(E), brave(E).

good_story(S, A, T) :- setting(S), activity(A), token(T), affords(S, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sname, s in SETTINGS.items():
        lines.append(asp.fact("setting", sname))
        if s.indoor:
            lines.append(asp.fact("indoor", sname))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sname, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for tid, t in TOKENS.items():
        lines.append(asp.fact("token", tid))
        lines.append(asp.fact("token_label", tid, t.label))
        if t.plural:
            lines.append(asp.fact("token_plural", tid))
        for g in sorted(t.genders):
            lines.append(asp.fact("wears", g, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld of silly misunderstanding, kindness, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.activity is None or c[1] == args.activity)
              and (args.token is None or c[2] == args.token)]
    if not combos:
        raise StoryError(explain_rejection())
    sname, act_id, tok_id = rng.choice(sorted(combos))
    tok = TOKENS[tok_id]
    gender = args.gender or rng.choice(sorted(tok.genders))
    if args.gender and args.gender not in tok.genders:
        raise StoryError("(No story: that token does not fit that child here.)")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=sname, activity=act_id, token=tok_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(SETTINGS[params.setting], ACTIVITIES[params.activity], TOKENS[params.token],
                              params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sname, act_id, tok_id in valid_combos():
            p = StoryParams(
                setting=sname,
                activity=act_id,
                token=tok_id,
                name="Mia",
                gender="girl",
                helper="Noah",
                trait="curious",
            )
            samples.append(generate(p))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
