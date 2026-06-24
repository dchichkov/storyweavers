#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about sharing, a mistaken list, and a happy fix.

Premise:
- A child or young helper in a small fairy-tale place wants to share a basket
  of treats or toys with others.
- Someone finds a "list" and misunderstands it, thinking it is a list of rules
  about who gets what, or a list of names that excludes a friend.
- The misunderstanding creates hurt feelings and a small delay.
- The hero explains the list, shares openly, and the group ends with a warm,
  positive image.

This world keeps the state small and concrete:
- physical meters: items can be gathered, divided, delivered
- emotional memes: kindness, worry, confusion, relief, gratitude

The prose is driven by the simulated world state, not a frozen template.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "fairy", "mother"}
        male = {"boy", "prince", "king", "elf", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the mossy lane"
    name: str = "mossy lane"


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    list_kind: str
    share_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": Setting(place="the rose garden", name="rose garden"),
    "forest": Setting(place="the silver forest", name="silver forest"),
    "castle": Setting(place="the little castle courtyard", name="castle courtyard"),
    "village": Setting(place="the village green", name="village green"),
}

LIST_KINDS = {
    "gift_list": {
        "noun": "gift list",
        "misread": "a list of who should get the gifts first",
    },
    "sharing_list": {
        "noun": "sharing list",
        "misread": "a list that tells one friend they may not join",
    },
    "help_list": {
        "noun": "help list",
        "misread": "a list of chores that sounds stern at first",
    },
}

SHARE_KINDS = {
    "apple_tarts": {
        "label": "apple tarts",
        "phrase": "warm apple tarts",
        "plural": True,
        "count": 4,
    },
    "flowers": {
        "label": "wildflowers",
        "phrase": "little wildflowers tied with ribbon",
        "plural": True,
        "count": 6,
    },
    "candles": {
        "label": "candles",
        "phrase": "small honey candles",
        "plural": True,
        "count": 3,
    },
    "buttons": {
        "label": "buttons",
        "phrase": "bright buttons from a sewing basket",
        "plural": True,
        "count": 8,
    },
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Elsa", "Pippa", "Sera"]
BOY_NAMES = ["Robin", "Tobin", "Finn", "Oren", "Bram", "Evan"]


# ---------------------------------------------------------------------------
# Fairytale prose helpers
# ---------------------------------------------------------------------------

def first_name(hero: Entity) -> str:
    return hero.id


def title_word(hero: Entity) -> str:
    return {"girl": "girl", "boy": "boy", "princess": "princess", "prince": "prince"}.get(hero.type, hero.type)


def intro_line(hero: Entity, friend: Entity, setting: Setting) -> str:
    return (
        f"Once upon a soft morning in {setting.place}, a gentle {title_word(hero)} named {first_name(hero)} "
        f"met a kind {title_word(friend)} named {first_name(friend)}."
    )


def list_line(world: World) -> str:
    hero = world.get("hero")
    list_ent = world.get("list")
    return (
        f"{first_name(hero)} carried a {list_ent.label}, and {hero.pronoun('possessive')} heart felt bright "
        f"because sharing was part of the day's plan."
    )


def share_line(world: World) -> str:
    hero = world.get("hero")
    share = world.get("share")
    return f"{first_name(hero)} brought out {share.phrase}, ready to share them with a smile."


def misunderstanding_line(world: World) -> str:
    hero = world.get("hero")
    friend = world.get("friend")
    list_ent = world.get("list")
    friend.memes["confusion"] = friend.memes.get("confusion", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    return (
        f"When {first_name(friend)} saw the {list_ent.label}, {friend.pronoun().capitalize()} frowned a little. "
        f"{friend.pronoun().capitalize()} thought the {list_ent.label} was a rule that meant {first_name(friend)} should stay back."
    )


def gentle_warning_line(world: World) -> str:
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    return (
        f"{first_name(hero)} noticed the worried face at once and spoke softly, so the air would not turn sharp."
    )


def explain_line(world: World) -> str:
    hero = world.get("hero")
    friend = world.get("friend")
    list_ent = world.get("list")
    share = world.get("share")
    return (
        f'"This is only my {list_ent.label}," said {first_name(hero)}. '
        f'"It is a kind list for sharing {share.phrase}, not a list for leaving you out."'
    )


def joy_line(world: World) -> str:
    hero = world.get("hero")
    friend = world.get("friend")
    share = world.get("share")
    friend.memes["relief"] = friend.memes.get("relief", 0) + 1
    friend.memes["gratitude"] = friend.memes.get("gratitude", 0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    return (
        f"{first_name(friend)} smiled wide, and the two of them shared the {share.label} together, "
        f"as if the sun itself had leaned closer to listen."
    )


def ending_line(world: World) -> str:
    hero = world.get("hero")
    friend = world.get("friend")
    share = world.get("share")
    return (
        f"By evening, the {share.label} was gone, but the kindness stayed. "
        f"{first_name(hero)} and {first_name(friend)} walked home with light steps and happy hearts."
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.list_kind not in LIST_KINDS:
        raise StoryError(f"Unknown list kind: {params.list_kind}")
    if params.share_kind not in SHARE_KINDS:
        raise StoryError(f"Unknown sharing kind: {params.share_kind}")

    world = World(SETTINGS[params.setting])

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"sharing": 0.0},
        memes={"kindness": 1.0, "hope": 1.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_type,
        label=params.friend_name,
        meters={"sharing": 0.0},
        memes={"trust": 1.0},
    ))
    list_ent = world.add(Entity(
        id="list",
        type="thing",
        label=LIST_KINDS[params.list_kind]["noun"],
        phrase=LIST_KINDS[params.list_kind]["misread"],
        owner=hero.id,
        meters={"paper": 1.0},
    ))
    share = world.add(Entity(
        id="share",
        type="thing",
        label=SHARE_KINDS[params.share_kind]["label"],
        phrase=SHARE_KINDS[params.share_kind]["phrase"],
        plural=SHARE_KINDS[params.share_kind]["plural"],
        owner=hero.id,
        carried_by=hero.id,
        meters={"amount": float(SHARE_KINDS[params.share_kind]["count"])},
    ))

    world.facts.update(hero=hero, friend=friend, list_ent=list_ent, share=share, params=params)

    world.say(intro_line(hero, friend, world.setting))
    world.say(list_line(world))
    world.say(share_line(world))
    world.para()

    world.say(misunderstanding_line(world))
    world.say(gentle_warning_line(world))
    hero.memes["concern"] = hero.memes.get("concern", 0) + 1
    world.para()

    world.say(explain_line(world))
    hero.meters["sharing"] += 1
    share.meters["amount"] = 0.0
    world.say(joy_line(world))
    world.say(ending_line(world))

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a short fairy tale about {p.hero_name} and a misunderstanding over a {LIST_KINDS[p.list_kind]['noun']}.",
        f"Tell a gentle story where a shared {SHARE_KINDS[p.share_kind]['label']} is mistaken for a rule, then explained kindly.",
        f"Write a positive fairy tale in which two friends clear up confusion about a list and end by sharing together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    list_ent: Entity = world.facts["list_ent"]  # type: ignore[assignment]
    share: Entity = world.facts["share"]  # type: ignore[assignment]
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What did {hero.label} bring that caused the misunderstanding?",
            answer=f"{hero.label} brought a {list_ent.label}, and {friend.label} first thought it meant something unkind."
        ),
        QAItem(
            question=f"What was {hero.label} really planning to do with the {share.label}?",
            answer=f"{hero.label} was planning to share the {share.label} with {friend.label}."
        ),
        QAItem(
            question=f"How did the misunderstanding end in {world.setting.place}?",
            answer=f"{hero.label} explained that the {list_ent.label} was only a helpful {LIST_KINDS[p.list_kind]['noun']}, and then they shared the {share.label} together."
        ),
        QAItem(
            question=f"How did {friend.label} feel after the truth was explained?",
            answer=f"{friend.label} felt relieved and grateful, because the list was never meant to leave {friend.label} out."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is a list?",
            answer="A list is a set of words or items written down together, often to help someone remember things."
        ),
        QAItem(
            question="Why can a list sometimes cause a misunderstanding?",
            answer="A list can cause a misunderstanding when someone guesses the wrong meaning before they ask what it really says."
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people enjoy or use something with you, so more than one person can take part."
        ),
        QAItem(
            question="Why is sharing usually a kind thing?",
            answer="Sharing is usually kind because it helps everyone feel included and cared for."
        ),
        QAItem(
            question=f"What kind of fairy-tale feeling does a {LIST_KINDS[p.list_kind]['noun']} give this story?",
            answer="It gives the story a gentle, small mystery that can be fixed with kindness and a clear explanation."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about sharing and misunderstanding.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "princess", "prince"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy", "princess", "prince"])
    ap.add_argument("--list-kind", choices=sorted(LIST_KINDS))
    ap.add_argument("--share-kind", choices=sorted(SHARE_KINDS))
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    list_kind = args.list_kind or rng.choice(sorted(LIST_KINDS))
    share_kind = args.share_kind or rng.choice(sorted(SHARE_KINDS))

    hero_type = args.hero_type or rng.choice(["girl", "boy", "princess", "prince"])
    friend_type = args.friend_type or rng.choice(["girl", "boy", "princess", "prince"])

    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type in {"girl", "princess"} else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])

    if args.hero_type and args.friend_type and args.hero_type == args.friend_type and args.hero_name and args.friend_name:
        pass

    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        list_kind=list_kind,
        share_kind=share_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(garden;forest;castle;village).
list_kind(gift_list;sharing_list;help_list).
share_kind(apple_tarts;flowers;candles;buttons).

% A story is valid when it has a real setting, a real list, and a shareable treasure.
valid_story(S,L,T) :- setting(S), list_kind(L), share_kind(T).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for k in LIST_KINDS:
        lines.append(asp.fact("list_kind", k))
    for k in SHARE_KINDS:
        lines.append(asp.fact("share_kind", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    py = sorted((s, l, t) for s in SETTINGS for l in LIST_KINDS for t in SHARE_KINDS)
    if set(atoms) == set(py):
        print(f"OK: ASP and Python agree on {len(py)} valid story combinations.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = []
        for s in sorted(SETTINGS):
            for l in sorted(LIST_KINDS):
                for t in sorted(SHARE_KINDS):
                    p = StoryParams(
                        setting=s,
                        hero_name="Lina",
                        hero_type="girl",
                        friend_name="Robin",
                        friend_type="boy",
                        list_kind=l,
                        share_kind=t,
                    )
                    samples.append(generate(p))
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
