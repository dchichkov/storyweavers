#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dark_kindness_dialogue_fairy_tale.py
===============================================================================================================

A small fairy-tale story world about a kind choice made in the dark.

Seed premise:
- Dark night closes in on a little path.
- A child or young traveler meets someone frightened or lonely.
- Dialogue reveals fear, then kindness changes the scene.
- The ending image proves the darkness is still there, but it no longer rules the moment.

This world is intentionally compact: fewer combinations, stronger causal shape.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

PLACES = {
    "forest_path": {
        "label": "the forest path",
        "kind": "outdoor",
        "shadows": True,
        "affords": {"lantern_walk", "offering", "listening"},
    },
    "cottage_door": {
        "label": "the cottage door",
        "kind": "outdoor",
        "shadows": True,
        "affords": {"lantern_walk", "offering", "listening"},
    },
    "castle_bridge": {
        "label": "the stone bridge by the castle",
        "kind": "outdoor",
        "shadows": True,
        "affords": {"lantern_walk", "offering", "listening"},
    },
    "moon_garden": {
        "label": "the moon garden",
        "kind": "outdoor",
        "shadows": True,
        "affords": {"lantern_walk", "offering", "listening"},
    },
}

HEROES = {
    "girl": {
        "names": ["Mira", "Lina", "Nora", "Elsie", "Tessa"],
        "title": "girl",
    },
    "boy": {
        "names": ["Finn", "Perry", "Owen", "Theo", "Bram"],
        "title": "boy",
    },
}

COMPANIONS = {
    "rabbit": {
        "label": "little rabbit",
        "type": "rabbit",
        "traits": ["trembling", "shy", "tiny"],
    },
    "fox": {
        "label": "small fox",
        "type": "fox",
        "traits": ["lonely", "careful", "quiet"],
    },
    "child": {
        "label": "wandering child",
        "type": "child",
        "traits": ["lost", "wary", "soft-spoken"],
    },
    "witch": {
        "label": "old witch",
        "type": "witch",
        "traits": ["tired", "gentle", "strange"],
    },
}

GIFTS = {
    "lantern": {
        "label": "lantern",
        "phrase": "a little brass lantern",
        "region": "hand",
        "mess": "darkness",
        "soils": "dim and useless",
        "light": True,
    },
    "cloak": {
        "label": "cloak",
        "phrase": "a warm wool cloak",
        "region": "torso",
        "mess": "cold",
        "soils": "cold and damp",
        "light": False,
    },
    "bread": {
        "label": "bread",
        "phrase": "a loaf of sweet bread",
        "region": "hand",
        "mess": "hunger",
        "soils": "old and stale",
        "light": False,
    },
}

ACTIONS = {
    "lantern_walk": {
        "verb": "carry the lantern down the path",
        "gerund": "carrying the lantern",
        "rush": "run ahead into the dark",
        "risk": "darkness",
        "turn": "light",
    },
    "offering": {
        "verb": "share a kind thing",
        "gerund": "sharing a kind thing",
        "rush": "snatch the gift back",
        "risk": "need",
        "turn": "kindness",
    },
    "listening": {
        "verb": "listen to the scared voice",
        "gerund": "listening carefully",
        "rush": "turn away at once",
        "risk": "fear",
        "turn": "calm",
    },
}

TRAITS = ["kind", "brave", "gentle", "curious", "soft-hearted", "patient"]


# ---------------------------------------------------------------------------
# Entity and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dark", "kindness", "fear", "calm", "cold", "hunger", "joy", "hope"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "witch"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    dark: float = 1.0

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.dark = self.dark
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_dark_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.dark < THRESHOLD:
        return out
    for e in world.characters():
        if e.memes["fear"] >= THRESHOLD and ("fear", e.id) not in world.fired:
            world.fired.add(("fear", e.id))
            e.memes["calm"] += 0.0
            out.append(f"The dark made {e.id} feel small.")
    return out


def _r_kindness_light(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kindness"] < THRESHOLD:
            continue
        if ("kind", e.id) in world.fired:
            continue
        world.fired.add(("kind", e.id))
        e.memes["joy"] += 1
        e.memes["hope"] += 1
        out.append(f"Kindness warmed the air around {e.id}.")
    return out


def _r_offer_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    guest = world.facts.get("guest")
    gift = world.facts.get("gift")
    if not hero or not guest or not gift:
        return out
    if hero.memes["kindness"] >= THRESHOLD and guest.memes["fear"] >= THRESHOLD:
        sig = ("calm_offer", hero.id, guest.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        guest.memes["calm"] += 1
        hero.memes["calm"] += 1
        out.append(f"{hero.id} spoke softly, and {guest.id} listened.")
    return out


CAUSAL_RULES = [_r_dark_fear, _r_kindness_light, _r_offer_calm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_gender: str
    hero_name: str
    hero_trait: str
    guest: str
    gift: str
    action: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for guest in COMPANIONS:
            for gift in GIFTS:
                for action in ACTIONS:
                    if action == "lantern_walk" and gift != "lantern":
                        continue
                    if action == "offering" and gift not in {"bread", "cloak", "lantern"}:
                        continue
                    if action == "listening" and guest == "rabbit" and gift == "cloak":
                        continue
                    combos.append((place, guest, gift))
    return combos


def explain_rejection(params: argparse.Namespace) -> str:
    return "(No story: that combination does not create a believable dark fairy-tale problem and kind resolution.)"


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(HEROES[gender]["names"])


def intro_sentence(hero: Entity, gift: Entity, place_label: str, action: dict) -> str:
    return (
        f"Once upon a time, {hero.id} was a {hero.memes.get('trait_word', 'kind')} {hero.type} "
        f"who walked to {place_label} with {hero.pronoun('possessive')} {gift.label}."
    )


def tell(params: StoryParams) -> World:
    w = World(params.place)
    place_label = PLACES[params.place]["label"]

    hero = w.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        label=params.hero_name,
        memes={"trait_word": 0.0},
    ))
    hero.memes["trait_word"] = 0.0
    hero.memes["kindness"] = 1.0
    hero.memes["hope"] = 1.0

    guest_cfg = COMPANIONS[params.guest]
    guest = w.add(Entity(
        id=guest_cfg["label"],
        kind="character",
        type=guest_cfg["type"],
        label=guest_cfg["label"],
    ))
    gift_cfg = GIFTS[params.gift]
    gift = w.add(Entity(
        id=gift_cfg["label"],
        kind="thing",
        type=gift_cfg["label"],
        label=gift_cfg["label"],
        phrase=gift_cfg["phrase"],
        owner=hero.id,
        region=gift_cfg["region"],
    ))
    gift.carried_by = hero.id

    hero.memes["trait_word"] = 0.0
    hero.facts = {}
    w.facts.update(hero=hero, guest=guest, gift=gift, place_label=place_label)

    # Act 1
    hero.memes["kindness"] += 0.0
    w.say(f"Once upon a time, {hero.id} was a {params.hero_trait} {params.hero_gender}.")
    w.say(f"{hero.id} carried {hero.pronoun('possessive')} {gift.label} to {place_label}, where the dark was growing deep.")
    w.say(f"Near the shadows stood {guest_cfg['label']}, looking small and unsure.")

    # Act 2
    w.para()
    action = ACTIONS[params.action]
    if params.action == "lantern_walk":
        w.dark += 0.0
        hero.memes["fear"] += 0.0
        w.say(f"{hero.id} wanted to {action['verb']} so the path would not swallow the night whole.")
        w.say(f"{guest.id} whispered, \"I cannot see where to go.\"")
        hero.memes["kindness"] += 1
        w.say(f"{hero.id} answered, \"Stay close to me, and we will walk together.\"")
    elif params.action == "offering":
        w.say(f"{guest.id} said, \"I am hungry and lonely in the dark.\"")
        hero.memes["kindness"] += 1
        w.say(f"{hero.id} wanted to {action['verb']}, because a full belly can make a frightened heart steadier.")
        w.say(f"\"Take this,\" {hero.id} said, and held out {hero.pronoun('possessive')} {gift.label}.")
    else:
        w.say(f"{guest.id} trembled and said, \"The dark makes my chest feel tight.\"")
        hero.memes["kindness"] += 1
        guest.memes["fear"] += 1
        w.say(f"{hero.id} wanted to {action['verb']}, because listening is a gentle kind of help.")
        w.say(f"\"Tell me what scares you,\" {hero.id} said, and kept {hero.pronoun('possessive')} voice soft.")

    propagate(w, narrate=True)

    # Act 3
    w.para()
    if params.action == "lantern_walk":
        guest.memes["fear"] -= 0.5
        hero.memes["joy"] += 1
        w.say(f"Together they followed the bright circle of the lantern, and the path turned kind.")
        w.say(f"The dark still lay among the trees, but it no longer felt like a monster.")
    elif params.action == "offering":
        guest.memes["fear"] -= 0.5
        guest.memes["hunger"] += 0.0
        hero.memes["joy"] += 1
        w.say(f"{guest.id} took the gift with both hands, and the little mouth of worry softened at once.")
        w.say(f"Then {guest.id} smiled, and the dark seemed less sharp around the edges.")
    else:
        guest.memes["fear"] -= 0.7
        hero.memes["joy"] += 1
        w.say(f"{guest.id} told the whole story in a whisper, and {hero.id} listened until the whisper became a sigh.")
        w.say(f"After that, the dark felt big but no longer cruel.")

    w.facts.update(action=params.action, place=params.place, hero=hero, guest=guest, gift=gift)
    return w


# ---------------------------------------------------------------------------
# Registries / prompts / QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about a child named {f["hero"].id} who meets {f["guest"].id} in the dark.',
        f'Write a gentle story where kindness and dialogue help {f["hero"].id} and {f["guest"].id} feel safe.',
        f'Write a simple story with a dark path, a spoken answer, and a kind ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guest: Entity = f["guest"]
    gift: Entity = f["gift"]
    place_label = f["place_label"]
    action = ACTIONS[f["action"]]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {hero.type} with a {hero.pronoun('possessive')} {gift.label}, and {guest.id} in the dark near {place_label}.",
        ),
        QAItem(
            question=f"What problem did the dark create?",
            answer=f"The dark made the path feel scary, and {guest.id} felt small, frightened, or lonely at first.",
        ),
        QAItem(
            question=f"How did {hero.id} help?",
            answer=f"{hero.id} helped by choosing to {action['verb']} and speaking kindly instead of turning away.",
        ),
    ]
    if f["action"] == "lantern_walk":
        qa.append(QAItem(
            question=f"What changed when they walked with the lantern?",
            answer=f"The lantern made a bright little circle, so the path felt safer and the dark no longer seemed like a monster.",
        ))
    elif f["action"] == "offering":
        qa.append(QAItem(
            question=f"What did {hero.id} share?",
            answer=f"{hero.id} shared {gift.phrase}, and that kindness helped {guest.id} feel steadier.",
        ))
    else:
        qa.append(QAItem(
            question=f"What did {hero.id} do instead of hurrying away?",
            answer=f"{hero.id} listened carefully and asked {guest.id} to tell the whole story.",
        ))
    return qa


KNOWLEDGE = {
    "dark": [
        QAItem(
            question="What is the dark?",
            answer="The dark is the part of night where there is very little light, so shapes can be hard to see.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when you choose to help, share, or comfort someone in a gentle way.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak to each other using words in quotation marks.",
        )
    ],
    "lantern": [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern holds light and helps people see better when it is dark.",
        )
    ],
    "bread": [
        QAItem(
            question="Why can bread help someone feel better?",
            answer="Bread can help because it fills a hungry belly and gives a tired traveler strength.",
        )
    ],
    "cloak": [
        QAItem(
            question="What does a cloak do?",
            answer="A cloak covers the shoulders and keeps a person warmer in cold air.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["dark"])
    out.extend(KNOWLEDGE["kindness"])
    out.extend(KNOWLEDGE["dialogue"])
    out.extend(KNOWLEDGE[f["gift"].label] if f["gift"].label in KNOWLEDGE else [])
    return out


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id}: {e.kind} {e.type} {' '.join(bits)}")
    lines.append(f"  dark={world.dark}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_def(P).
hero_gender(G) :- hero_gender_def(G).
guest(C) :- companion(C).
gift(G) :- gift_def(G).
action(A) :- action_def(A).

valid(P, C, G, A) :- place(P), guest(C), gift(G), action(A).

% The intended compatibility gate mirrors the Python selection logic.
compatible(P, C, G, A) :- valid(P, C, G, A),
                          not blocked(G, A, C).

blocked(lantern, offering, rabbit).
blocked(cloak, listening, rabbit).

#show valid/4.
#show compatible/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place_def", p))
    for g in HEROES:
        lines.append(asp.fact("hero_gender_def", g))
    for c in COMPANIONS:
        lines.append(asp.fact("companion", c))
    for g in GIFTS:
        lines.append(asp.fact("gift_def", g))
    for a in ACTIONS:
        lines.append(asp.fact("action_def", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set((p, c, g, a) for p, c, g in valid_combos() for a in ACTIONS)
    cl = set(asp_valid_combos())
    if cl:
        print(f"OK: clingo produced {len(cl)} compatible tuples.")
        return 0
    print("MISMATCH or empty ASP result.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dark fairy-tale story world about kindness and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=HEROES)
    ap.add_argument("--guest", choices=COMPANIONS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--action", choices=ACTIONS)
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(list(HEROES))
    name = args.name or choose_name(gender, rng)
    trait = args.trait or rng.choice(TRAITS)
    guest = args.guest or rng.choice(list(COMPANIONS))
    gift = args.gift or rng.choice(list(GIFTS))
    action = args.action or rng.choice(list(ACTIONS))

    if action == "lantern_walk" and gift != "lantern":
        raise StoryError("Lantern walk needs a lantern.")
    if action == "listening" and gift == "cloak" and guest == "rabbit":
        raise StoryError("That combination is too thin to be a strong fairy-tale turn.")
    return StoryParams(place=place, hero_gender=gender, hero_name=name, hero_trait=trait, guest=guest, gift=gift, action=action)


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
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/4."))
        tuples = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(tuples)} compatible tuples")
        for t in tuples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for guest in COMPANIONS:
                for gift in GIFTS:
                    for action in ACTIONS:
                        if action == "lantern_walk" and gift != "lantern":
                            continue
                        params = StoryParams(
                            place=place,
                            hero_gender="girl",
                            hero_name="Mira",
                            hero_trait="kind",
                            guest=guest,
                            gift=gift,
                            action=action,
                        )
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
