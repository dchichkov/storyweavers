#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cranium_abs_vacant_sound_effects_sharing_quest.py
==============================================================================================================

A small fable-style story world about a quest, a sound-filled trail, and a
compromise built through sharing.

Seed-image premise:
- A clever childlike creature has a proud cranium, strong abs, and a vacant
  little satchel.
- Friends set out on a quest to find a lost lantern for a quiet hollow.
- Along the way, they make sound effects, need to share supplies, and learn
  that a vacant place can become welcoming when they work together.

This script is self-contained and follows the Storyweavers world contract.
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "fox", "hare", "owl"}
        female = {"girl", "mother", "mom", "woman", "deer", "bear"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    vacancy: str
    echo: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    useful_for: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    helps: set[str]
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.stage: str = "start"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "woods": Place(id="woods", label="the woods", vacancy="vacant clearing", echo="soft echo", affords={"quest"}),
    "hollow": Place(id="hollow", label="the hollow", vacancy="vacant hollow", echo="quiet echo", affords={"quest"}),
    "hill": Place(id="hill", label="the hill", vacancy="vacant hilltop", echo="long echo", affords={"quest"}),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        verb="find the lost lantern",
        gerund="finding the lost lantern",
        rush="dash toward the lantern glow",
        sound="clink-clink",
        keyword="lantern",
        tags={"sound", "share", "quest"},
    ),
    "bridgebell": Quest(
        id="bridgebell",
        verb="bring back the bridgebell",
        gerund="bringing back the bridgebell",
        rush="hurry to the bridge",
        sound="tap-tap",
        keyword="bell",
        tags={"sound", "share", "quest"},
    ),
    "seedkey": Quest(
        id="seedkey",
        verb="recover the seedkey",
        gerund="recovering the seedkey",
        rush="run to the old root",
        sound="pat-pat",
        keyword="seedkey",
        tags={"sound", "share", "quest"},
    ),
}

TOKENS = {
    "map": Token(id="map", label="map", phrase="a folded map", type="map", useful_for={"quest"}),
    "snack": Token(id="snack", label="snack", phrase="a small berry snack", type="snack", useful_for={"share"}),
    "lamp": Token(id="lamp", label="lamp", phrase="a little lamp", type="lamp", useful_for={"sound"}),
}

SHARES = {
    "berries": ShareItem(id="berries", label="berries", phrase="a bowl of berries", helps={"share"}),
    "rope": ShareItem(id="rope", label="rope", phrase="a loop of rope", helps={"quest"}),
    "song": ShareItem(id="song", label="song", phrase="a bright song", helps={"sound", "share"}),
}

NAMES = ["Milo", "Pip", "Luna", "Nora", "Toby", "Wren", "Bram", "Kiki"]
KINDS = ["fox", "hare", "owl", "deer", "bear"]
TRAITS = ["brave", "kind", "patient", "curious", "gentle", "nimble"]


def is_reasonable(place: Place, quest: Quest, token: Token, share: ShareItem) -> bool:
    return "quest" in place.affords and "quest" in quest.tags and "quest" in token.useful_for and "share" in share.helps


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for pid, place in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for tid, token in TOKENS.items():
                for sid, share in SHARES.items():
                    if is_reasonable(place, quest, token, share):
                        out.append((pid, qid, tid, sid))
    return out


@dataclass
class StoryParams:
    place: str
    quest: str
    token: str
    share: str
    name: str
    type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style quest about sound effects and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=KINDS)
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
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.token is None or c[2] == args.token)
              and (args.share is None or c[3] == args.share)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, quest, token, share = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    kind = args.type or rng.choice(KINDS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, token=token, share=share, name=name, type=kind, trait=trait)


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.type, traits=["small", params.trait]))
    friend = world.add(Entity(id="Friend", kind="character", type=rng_kind(params.name), traits=["helpful"]))
    token = world.add(Entity(id="Token", type=TOKENS[params.token].type, label=TOKENS[params.token].label, phrase=TOKENS[params.token].phrase, owner=hero.id))
    share = world.add(Entity(id="Share", type=SHARES[params.share].id, label=SHARES[params.share].label, phrase=SHARES[params.share].phrase, owner=hero.id))
    world.facts.update(hero=hero, friend=friend, token=token, share=share, quest=QUESTS[params.quest], params=params)
    hero.meters["abs"] = 2.0
    hero.meters["cranium"] = 1.0
    hero.meters["vacant"] = 1.0
    return world


def rng_kind(seed_text: str) -> str:
    return KINDS[sum(ord(c) for c in seed_text) % len(KINDS)]


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    quest = world.facts["quest"]
    token = world.facts["token"]
    share = world.facts["share"]

    world.say(f"{hero.id} was a {hero.traits[1]} {hero.type} with a sturdy cranium and strong abs.")
    world.say(f"But {hero.pronoun('possessive')} little pack was vacant, and the empty space made {hero.id} feel ready for a quest.")
    world.say(f"At {world.place.label}, {hero.id} met {friend.id}, and together they set out to {quest.verb}.")
    world.para()
    world.say(f"They went past the {world.place.vacancy}, and the trail answered with {quest.sound}, {quest.sound}, {quest.sound}.")
    hero.memes["wonder"] = 1.0
    hero.memes["hope"] = 1.0
    world.say(f"{hero.id} found {token.phrase}, but the path got tricky because one friend had the map and the other had the lamp.")
    world.say(f"So they shared {share.phrase}. That small act made the quest lighter, like two feet carrying one happy thought.")
    friend.memes["sharing"] = 1.0
    hero.memes["sharing"] = 1.0
    world.para()
    world.say(f"When they reached the {world.place.vacancy}, they used the shared help and the bright sound effect of {quest.sound} to place the token where it belonged.")
    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    world.say(f"The empty place did not stay empty. It became a warm home for the lost thing, and {hero.id} walked back smiling, with a fuller pack and a fuller heart.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f"Write a short fable about {hero.id}, a quest, and a vacant place that becomes welcoming.",
        f"Tell a child-friendly story where sound effects and sharing help a {hero.type} finish {quest.gerund}.",
        f"Create a simple moral tale that uses the words cranium, abs, and vacant naturally.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    place = world.place
    return [
        QAItem(
            question=f"Who goes on the quest in {place.label}?",
            answer=f"{hero.id} goes on the quest with a friend, and they travel through {place.vacancy}.",
        ),
        QAItem(
            question=f"What sound do they hear while {quest.gerund}?",
            answer=f"They hear {quest.sound} over and over as they move through the quiet place.",
        ),
        QAItem(
            question="How did sharing help the quest?",
            answer="Sharing made the work easier because the friends could use their things together instead of arguing over them.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The vacant place became useful and welcoming, and {hero.id} came home happy with a completed quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quest?", answer="A quest is a goal or journey to find, fix, or bring back something important."),
        QAItem(question="What are sound effects in a story?", answer="Sound effects are words that imitate noises, like tap-tap or clink-clink."),
        QAItem(question="What does sharing mean?", answer="Sharing means letting another person use or enjoy something too."),
        QAItem(question="What does vacant mean?", answer="Vacant means empty, with nobody or nothing inside."),
        QAItem(question="What is a cranium?", answer="A cranium is the bony part of the head that protects the brain."),
        QAItem(question="What are abs?", answer="Abs are the muscles in the front of the body that help a creature bend and sit up."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_id(Q).
token(T) :- token_id(T).
share(S) :- share_id(S).

reasonable(P,Q,T,S) :- setting(P), quest(Q), token(T), share(S),
                       affords(P, quest),
                       quest_tag(Q, quest),
                       token_useful(T, quest),
                       share_help(S, share).

#show reasonable/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("vacancy", pid, p.vacancy))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_id", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, t))
    for tid, t in TOKENS.items():
        lines.append(asp.fact("token_id", tid))
        for u in sorted(t.useful_for):
            lines.append(asp.fact("token_useful", tid, u))
    for sid, s in SHARES.items():
        lines.append(asp.fact("share_id", sid))
        for h in sorted(s.helps):
            lines.append(asp.fact("share_help", sid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="woods", quest="lantern", token="map", share="berries", name="Milo", type="fox", trait="brave"),
    StoryParams(place="hollow", quest="bridgebell", token="lamp", share="song", name="Luna", type="owl", trait="kind"),
    StoryParams(place="hill", quest="seedkey", token="snack", share="rope", name="Pip", type="hare", trait="curious"),
]


def explain_rejection() -> str:
    return "No story: this world needs a quest, a token, and a sharing choice that all support the same gentle fable."


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show reasonable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
