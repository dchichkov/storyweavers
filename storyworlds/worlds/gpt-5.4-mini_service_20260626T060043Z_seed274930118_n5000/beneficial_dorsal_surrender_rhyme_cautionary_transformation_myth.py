#!/usr/bin/env python3
"""
A small mythic storyworld about a proud child, a careful warning, a beneficial
surrender, and a transforming blessing.

The seed premise is: a young seeker finds a shining ridge-stone on a hill above
the sea. An elder warns that the stone belongs to the dorsal-backed river spirit.
When the seeker gives it back, the spirit rewards the surrender by transforming
the seeker, the village, and the road home.

This file is self-contained and follows the Storyweavers world contract.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place | spirit
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    opening: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    danger: str
    region: str
    blesses: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spirit:
    id: str
    label: str
    phrase: str
    gift: str
    transform: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "shore": Setting(
        name="the shore",
        opening="The shore met the sea with bright stones and salt wind.",
        affordances={"find", "warn", "return"},
    ),
    "temple": Setting(
        name="the hill temple",
        opening="The hill temple stood above the water like a watchful shell.",
        affordances={"find", "warn", "return"},
    ),
    "riverbank": Setting(
        name="the riverbank",
        opening="The riverbank hummed with reeds, frogs, and old songs.",
        affordances={"find", "warn", "return"},
    ),
}

RELICS = {
    "ridge_stone": Relic(
        id="ridge_stone",
        label="ridge-stone",
        phrase="a polished ridge-stone with a dorsal stripe",
        danger="the river would remember the taking",
        region="hand",
        blesses="the road home",
        tags={"dorsal", "beneficial", "cautionary"},
    ),
    "sea_shell": Relic(
        id="sea_shell",
        label="shell",
        phrase="a bright shell from the tide",
        danger="the tide would call for it back",
        region="hand",
        blesses="the singer's breath",
        tags={"rhyme", "cautionary"},
    ),
    "sun_key": Relic(
        id="sun_key",
        label="sun-key",
        phrase="a warm bronze key from the old altar",
        danger="the gate would stay shut without its promise",
        region="hand",
        blesses="the village well",
        tags={"beneficial", "transformation"},
    ),
}

SPIRITS = {
    "river_spirit": Spirit(
        id="river_spirit",
        label="river spirit",
        phrase="a dorsal-backed river spirit",
        gift="clear water for every home",
        transform="silver scales on the seeker’s sleeves",
        rhyme="What is held in pride may turn to tide; what is given back may guard the ride.",
        tags={"dorsal", "beneficial", "rhyme", "transformation"},
    ),
    "tide_mother": Spirit(
        id="tide_mother",
        label="tide mother",
        phrase="a tide mother with a moon-white laugh",
        gift="salt-sweet fish and lantern foam",
        transform="sea-green threads in the cloak",
        rhyme="Take with care, return with grace; the sea will smile upon your face.",
        tags={"rhyme", "cautionary"},
    ),
}

HERO_NAMES = ["Mira", "Nilo", "Sera", "Tavin", "Lio", "Anya", "Eran", "Pela"]
ELDER_NAMES = ["Grandmother", "Elder", "Aunt", "Guide"]
TRAITS = ["proud", "curious", "brave", "restless", "gentle"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    relic: str
    spirit: str
    hero_name: str
    hero_type: str
    elder_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
holds_relic(H, R) :- hero(H), relic(R), owns(H, R).
warning_needed(S, R) :- spirit(S), relic(R), risky(R).
beneficial_surrender(H, R, S) :- holds_relic(H, R), warning_needed(S, R), returns(H, R), blesses(S, R).
transforms(H, S) :- beneficial_surrender(H, _, S), gift(S).
valid_story(Setting, Relic, Spirit) :- setting(Setting), relic(Relic), spirit(Spirit),
                                       setting_affords(Setting, find),
                                       warning_needed(Spirit, Relic),
                                       blesses(Spirit, Relic).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("setting_affords", sid, a))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("risky", rid))
        lines.append(asp.fact("blesses", "river_spirit" if rid == "ridge_stone" else ("tide_mother" if rid == "sea_shell" else "river_spirit"), rid))
    for spid in SPIRITS:
        lines.append(asp.fact("spirit", spid))
        lines.append(asp.fact("gift", spid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((s, r, sp) for s, r, sp in valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} valid stories).")
        return 0
    print("Mismatch between ASP and Python gate.")
    print("Only in Python:", sorted(py - cl))
    print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, relic in RELICS.items():
            for spid, spirit in SPIRITS.items():
                if "rhyme" in spirit.tags and "cautionary" in relic.tags:
                    combos.append((sid, rid, spid))
    return combos


def explain_rejection(relic: Relic, spirit: Spirit) -> str:
    return (
        f"(No story: the {relic.label} and the {spirit.label} do not make a strong mythic turn "
        f"for this world. Choose the dorsal ridge-stone with the river spirit, or another pair "
        f"that can truly warn, surrender, and transform.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def predict_turn(world: World, hero: Entity, relic: Relic, spirit: Spirit) -> dict[str, bool]:
    sim = world.copy()
    simulate_find(sim, hero, relic, narrate=False)
    warned = simulate_warn(sim, hero, relic, spirit, narrate=False)
    surrendered = simulate_surrender(sim, hero, relic, spirit, narrate=False)
    transformed = simulate_transform(sim, hero, relic, spirit, narrate=False)
    return {"warned": warned, "surrendered": surrendered, "transformed": transformed}


def simulate_find(world: World, hero: Entity, relic: Relic, narrate: bool = True) -> None:
    hero.meters = getattr(hero, "meters", {})
    hero.meters["desire"] = hero.meters.get("desire", 0) + 1
    world.facts["found"] = relic.id
    if narrate:
        world.say(
            f"{hero.id} found {relic.phrase} on the path above {world.setting.name} and held it close."
        )


def simulate_warn(world: World, hero: Entity, relic: Relic, spirit: Spirit, narrate: bool = True) -> bool:
    if "cautionary" not in relic.tags:
        return False
    world.facts["warned"] = True
    if narrate:
        world.say(
            f"{world.facts['elder']} said, \"Leave it be; {relic.danger}.\" "
            f"The words were soft, but they landed like thunder."
        )
    return True


def simulate_surrender(world: World, hero: Entity, relic: Relic, spirit: Spirit, narrate: bool = True) -> bool:
    world.facts["surrendered"] = True
    hero.memes = getattr(hero, "memes", {})
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["pride"] = max(0, hero.memes.get("pride", 0) - 1)
    if narrate:
        world.say(
            f"{hero.id} took a breath and chose surrender instead of pride, returning the {relic.label}."
        )
    return True


def simulate_transform(world: World, hero: Entity, relic: Relic, spirit: Spirit, narrate: bool = True) -> bool:
    world.facts["transformed"] = True
    hero.meters = getattr(hero, "meters", {})
    hero.meters["shine"] = hero.meters.get("shine", 0) + 1
    hero.meters["courage"] = hero.meters.get("courage", 0) + 1
    if narrate:
        world.say(
            f"The {spirit.label} rose from the water and, in a bright transformation, gave {hero.id} {spirit.transform}."
        )
        world.say(
            f"The village praised the beneficial surrender, and the path home felt wider than before."
        )
    return True


def setup_line(world: World, hero: Entity, elder: Entity, relic: Relic) -> None:
    world.say(world.setting.opening)
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'young')} {hero.type} who loved anything that shone."
    )
    world.say(
        f"One day {hero.id} met {relic.phrase} near the stones, and {hero.pronoun('possessive')} hands trembled with wanting."
    )


def rhyme_line(spirit: Spirit) -> str:
    return f'"{spirit.rhyme}"'


def ending_line(world: World, hero: Entity, spirit: Spirit, relic: Relic) -> None:
    world.say(
        f"After that, {hero.id} carried no stolen stone, only a calm smile and {spirit.gift} in {hero.pronoun('possessive')} heart."
    )
    world.say(
        f"The {relic.label} returned to the water, and the myth said the path itself learned the rhyme."
    )


def tell(setting: Setting, relic: Relic, spirit: Spirit, hero_name: str, hero_type: str, elder_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id=elder_name, kind="character", type="elder", label=elder_name))
    spirit_ent = world.add(Entity(id=spirit.id, kind="spirit", type="spirit", label=spirit.label))
    relic_ent = world.add(Entity(id=relic.id, kind="thing", type="relic", label=relic.label, phrase=relic.phrase))

    hero.memes["trait"] = trait
    world.facts.update(hero=hero, elder=elder_name, spirit=spirit_ent, relic=relic_ent, setting=setting, trait=trait)

    setup_line(world, hero, elder, relic)
    world.para()
    simulate_find(world, hero, relic)
    simulate_warn(world, hero, relic, spirit)
    if world.facts.get("warned"):
        world.say(rhyme_line(spirit))
    world.say(f"{hero.id} listened, and the listening became a turning.")
    world.para()
    simulate_surrender(world, hero, relic, spirit)
    simulate_transform(world, hero, relic, spirit)
    ending_line(world, hero, spirit, relic)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children that uses the words "beneficial", "dorsal", and "surrender".',
        f"Tell a cautionary story where {f['hero'].id} finds a {f['relic'].label}, heeds an elder's warning, and earns a transformation.",
        f"Write a rhyme-filled myth about a {f['trait']} seeker, a river spirit, and a wise return.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    relic: Entity = world.facts["relic"]
    elder = world.facts["elder"]
    spirit: Entity = world.facts["spirit"]
    return [
        QAItem(
            question=f"What did {hero.id} find on the path?",
            answer=f"{hero.id} found {relic.phrase} on the path above {world.setting.name}.",
        ),
        QAItem(
            question=f"Who warned {hero.id} not to keep the {relic.label}?",
            answer=f"{elder} warned {hero.id} and said that the taking would wake old trouble.",
        ),
        QAItem(
            question=f"What happened after the beneficial surrender?",
            answer=f"The {spirit.label} gave {hero.id} a transformation, and the homeward road felt blessed and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does surrender mean in a kind story?",
            answer="In a kind story, surrender can mean giving something back or letting go so that things can become better.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when the ends of words sound alike, like song pieces that fit together.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change, like when someone becomes wiser, stronger, or takes on a new form.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.extend(world.trace)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="shore", relic="ridge_stone", spirit="river_spirit", hero_name="Mira", hero_type="girl", elder_name="Grandmother", trait="proud"),
    StoryParams(setting="riverbank", relic="sun_key", spirit="river_spirit", hero_name="Tavin", hero_type="boy", elder_name="Elder", trait="curious"),
    StoryParams(setting="temple", relic="sea_shell", spirit="tide_mother", hero_name="Anya", hero_type="girl", elder_name="Aunt", trait="restless"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: cautionary, rhyming, transformational.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.relic and args.spirit:
        relic = RELICS[args.relic]
        spirit = SPIRITS[args.spirit]
        if not ("rhyme" in spirit.tags and "cautionary" in relic.tags):
            raise StoryError(explain_rejection(relic, spirit))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.relic is None or c[1] == args.relic)
        and (args.spirit is None or c[2] == args.spirit)
    ]
    if not combos:
        raise StoryError("(No valid mythic combination matches the given options.)")
    setting, relic, spirit = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, relic=relic, spirit=spirit, hero_name=name, hero_type=gender, elder_name=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], RELICS[params.relic], SPIRITS[params.spirit], params.hero_name, params.hero_type, params.elder_name, params.trait)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for rid in RELICS:
            for spid in SPIRITS:
                if "rhyme" in SPIRITS[spid].tags and "cautionary" in RELICS[rid].tags:
                    out.append((sid, rid, spid))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(model)} atoms")
        for atom in model:
            print(atom)
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
