#!/usr/bin/env python3
"""
A small folk-tale storyworld about Eve and Criss, built around a rhyme dispute
that ends in reconciliation.

The world is intentionally simple:
- Two child-like characters: Eve and Criss
- One shared village setting
- A rhyme token that can be spoken, borrowed, kept, returned, or mended
- A social arc: teasing -> hurt -> apology -> reconciliation

The story generator simulates meters and memes so the prose is driven by state:
who has the rhyme token, who feels proud or hurt, whether the friendship is
strained, and how a gift or apology changes things at the end.
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
# Domain registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village_green": {
        "name": "the village green",
        "features": {"well", "path", "oak_tree"},
    },
    "lantern_square": {
        "name": "Lantern Square",
        "features": {"bench", "fountain", "lantern"},
    },
    "meadow_edge": {
        "name": "the meadow edge",
        "features": {"brook", "hedge", "stone"},
    },
}

RHYMES = {
    "bird_rhyme": {
        "token": "bird-rhyme",
        "rhyme_line": "A bird on a vine sang silver and fine.",
        "gift_line": "A bird on a vine shared a song so fine.",
        "repair_line": "A bird on a vine sang kindly and fine.",
        "topic": "bird",
        "style": "soft",
    },
    "moon_rhyme": {
        "token": "moon-rhyme",
        "rhyme_line": "The moon on a tune shone over the dune.",
        "gift_line": "The moon on a tune shone brighter at noon.",
        "repair_line": "The moon on a tune shone gentle and soon.",
        "topic": "moon",
        "style": "bright",
    },
    "river_rhyme": {
        "token": "river-rhyme",
        "rhyme_line": "The river ran nimble and laughed through the thimble.",
        "gift_line": "The river ran nimble and laughed with a dimple.",
        "repair_line": "The river ran nimble and flowed ever simple.",
        "topic": "river",
        "style": "lively",
    },
}

GIFTS = {
    "pebble_string": {
        "label": "a string of smooth pebbles",
        "kind": "pebbles",
        "mends": "hurt",
        "image": "a small loop of stones warming in a palm",
    },
    "honey_cake": {
        "label": "a honey cake",
        "kind": "cake",
        "mends": "hunger",
        "image": "a round cake with a sweet crust",
    },
    "blue_ribbon": {
        "label": "a blue ribbon",
        "kind": "ribbon",
        "mends": "pride",
        "image": "a ribbon that caught the light like a stream",
    },
}

NAMES = ["Eve", "Criss", "Mara", "Tobin", "Rin", "Perry", "Joss", "Nell"]


# ---------------------------------------------------------------------------
# Result/world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def emo(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class StoryParams:
    setting: str
    rhyme: str
    gift: str
    eve_name: str = "Eve"
    criss_name: str = "Criss"
    seed: Optional[int] = None


@dataclass
class World:
    setting: dict
    entities: dict[str, Entity] = field(default_factory=dict)
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


# ---------------------------------------------------------------------------
# Helper text
# ---------------------------------------------------------------------------

def setting_line(setting: dict) -> str:
    return f"{setting['name'].capitalize()} was quiet under the folk-tale sky."


def rhyme_line(rhyme: dict) -> str:
    return rhyme["rhyme_line"]


def gift_image(gift: dict) -> str:
    return gift["image"]


# ---------------------------------------------------------------------------
# State updates
# ---------------------------------------------------------------------------

def speak_rhyme(world: World, speaker: Entity, rhyme: dict, shared: Entity) -> None:
    speaker.meters["pride"] = speaker.meters.get("pride", 0.0) + 1.0
    shared.memes["attention"] = shared.memes.get("attention", 0.0) + 1.0
    world.say(
        f"{speaker.id} said the rhyme aloud: “{rhyme_line(rhyme)}”"
    )


def tease(world: World, speaker: Entity, listener: Entity, rhyme: dict, shared: Entity) -> None:
    speaker.meters["pride"] = speaker.meters.get("pride", 0.0) + 1.0
    listener.memes["hurt"] = listener.memes.get("hurt", 0.0) + 1.0
    listener.memes["distance"] = listener.memes.get("distance", 0.0) + 1.0
    shared.meters["token_with_speaker"] = 1.0
    world.say(
        f"{speaker.id} kept the rhyme to {speaker.id.lower()}self and laughed at {listener.id}."
    )
    world.say(
        f"{listener.id} went quiet, because the joke stung like a thorn in a sleeve."
    )


def apologize(world: World, speaker: Entity, listener: Entity, gift: dict, rhyme: dict, shared: Entity) -> None:
    speaker.meters["humility"] = speaker.meters.get("humility", 0.0) + 1.0
    speaker.memes["regret"] = speaker.memes.get("regret", 0.0) + 1.0
    listener.memes["softening"] = listener.memes.get("softening", 0.0) + 1.0
    world.say(
        f"{speaker.id} came back with {gift['label']} and said, “I was unkind. I am sorry.”"
    )
    world.say(
        f"The little gift looked like {gift_image(gift)}, and the angry air began to thin."
    )
    world.say(
        f"{speaker.id} offered the rhyme back in a gentler way: “{rhyme['repair_line']}”"
    )
    shared.meters["token_shared"] = 1.0


def reconcile(world: World, eve: Entity, criss: Entity, rhyme: dict, gift: dict, shared: Entity) -> None:
    eve.memes["hurt"] = 0.0
    criss.memes["hurt"] = 0.0
    eve.memes["joy"] = eve.memes.get("joy", 0.0) + 1.0
    criss.memes["joy"] = criss.memes.get("joy", 0.0) + 1.0
    eve.memes["friendship"] = eve.memes.get("friendship", 0.0) + 1.0
    criss.memes["friendship"] = criss.memes.get("friendship", 0.0) + 1.0
    shared.meters["reconciled"] = 1.0
    world.say(
        f"Eve and Criss stood together again, and the rhyme sounded sweeter than before."
    )
    world.say(
        f"They shared the {gift['kind']}, and the day felt whole once more."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    rhyme = RHYMES[params.rhyme]
    gift = GIFTS[params.gift]
    world = World(setting=setting)

    eve = world.add(Entity(id=params.eve_name, kind="character", label="Eve"))
    criss = world.add(Entity(id=params.criss_name, kind="character", label="Criss"))
    shared = world.add(Entity(id="shared", kind="thing", label=rhyme["token"], owner=eve.id))
    gift_ent = world.add(Entity(id="gift", kind="thing", label=gift["label"], owner=criss.id))

    world.facts.update(
        setting=params.setting,
        rhyme=params.rhyme,
        gift=params.gift,
        eve=eve,
        criss=criss,
        shared=shared,
        gift_ent=gift_ent,
        rhyme_data=rhyme,
        gift_data=gift,
    )

    world.say(setting_line(setting))
    world.say(
        f"Eve and Criss found a small rhyme-token called the {rhyme['token']} near the path."
    )
    world.say(
        f"At first, both of them liked how the words shimmered in the air."
    )

    world.para()
    speak_rhyme(world, eve, rhyme, shared)
    tease(world, criss, eve, rhyme, shared)

    world.para()
    world.say(
        f"By evening, Criss felt bad about the hurt that had grown between them."
    )
    apologize(world, criss, eve, gift, rhyme, shared)
    reconcile(world, eve, criss, rhyme, gift, shared)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short folk tale for a young child about two friends who quarrel over a rhyme and then reconcile.',
        f"Tell a gentle story where Eve and Criss share the {f['rhyme_data']['token']} and end as friends again.",
        f"Write a simple folk tale that includes a {f['gift_data']['label']} and a kind apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rhyme = f["rhyme_data"]
    gift = f["gift_data"]
    eve = f["eve"]
    criss = f["criss"]

    return [
        QAItem(
            question="Who were the two friends in the story?",
            answer="The story was about Eve and Criss, two friends who met in a quiet folk-tale place.",
        ),
        QAItem(
            question=f"What did Eve and Criss argue about?",
            answer=f"They argued about the {rhyme['token']}, a small rhyme that sounded lovely at first.",
        ),
        QAItem(
            question="Why did the argument hurt Eve?",
            answer="It hurt Eve because Criss kept the rhyme to Criss self and laughed instead of sharing kindly.",
        ),
        QAItem(
            question="What did Criss bring to make things better?",
            answer=f"Criss brought {gift['label']}, which helped show real regret and made the air softer.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with Eve and Criss standing together again, sharing the rhyme and feeling like friends.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line of words that sounds musical because the ending sounds match or nearly match.",
        ),
        QAItem(
            question="Why do apologies matter?",
            answer="An apology matters because it shows someone understands they caused hurt and wants to make things right.",
        ),
        QAItem(
            question="What helps friends reconcile?",
            answer="Friends can reconcile when they speak honestly, show regret, and make a kind gesture or gift.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(village_green; lantern_square; meadow_edge).

rhyme(bird_rhyme; moon_rhyme; river_rhyme).
gift(pebble_string; honey_cake; blue_ribbon).

pairing(S, R, G) :- setting(S), rhyme(R), gift(G).
reconciles(R, G) :- rhyme(R), gift(G).

#show pairing/3.
#show reconciles/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show pairing/3."))
    return sorted(set(asp.atoms(model, "pairing")))


def asp_verify() -> int:
    py = {(s, r, g) for s in SETTINGS for r in RHYMES for g in GIFTS}
    cl = set(asp_pairs())
    if py == cl:
        print(f"OK: ASP matches Python pairing count ({len(py)}).")
        return 0
    print("Mismatch between ASP and Python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld of rhyme and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--eve", dest="eve_name")
    ap.add_argument("--criss", dest="criss_name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    rhyme = args.rhyme or rng.choice(list(RHYMES))
    gift = args.gift or rng.choice(list(GIFTS))
    eve_name = args.eve_name or "Eve"
    criss_name = args.criss_name or "Criss"
    if eve_name.lower() == criss_name.lower():
        raise StoryError("Eve and Criss must be different names.")
    return StoryParams(setting=setting, rhyme=rhyme, gift=gift, eve_name=eve_name, criss_name=criss_name)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {ent.kind} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams(setting="village_green", rhyme="bird_rhyme", gift="pebble_string"),
        StoryParams(setting="lantern_square", rhyme="moon_rhyme", gift="blue_ribbon"),
        StoryParams(setting="meadow_edge", rhyme="river_rhyme", gift="honey_cake"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show pairing/3.\n#show reconciles/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_pairs()
        print(f"{len(pairs)} ASP pairings:")
        for p in pairs:
            print(" ", p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
