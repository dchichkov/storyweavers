#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/span_deceive_pro_conflict_fairy_tale.py
============================================================================================================================

A standalone *story world* sketch for fairy tales about a deceptive span, a
clever pro, and a conflict that must be resolved through honest work.

Initial story (used to build a world model):
---
Once upon a time, in a valley of golden hills, a young weaver named Elara lived
with her grandmother. Elara wove beautiful blankets from wool, and she was proud
of her work. One day, a trickster merchant came to the valley. He saw Elara's
blankets and smiled a sly smile.

"This span of cloth is fine," said the merchant, "but I can double your wool
if you let me show you a secret." Elara was curious and agreed. The merchant
took her wool and replaced it with a thin, brittle thread that looked like wool
but would break after one wash. "Now weave faster," he said, "and sell more!"

But Elara's grandmother saw the deception. "Child," she said, "this thread will
not last. The merchant is trying to deceive you into making poor blankets. A
true pro values their craft and never trades quality for speed." Elara felt
torn. She wanted to please the merchant, but she also wanted to make good
blankets. The conflict burned in her heart.

In the end, Elara chose to be a pro. She returned the bad thread, wove only with
honest wool, and confronted the merchant. The valley praised her skill, and the
merchant left ashamed. Elara learned that a true pro never deceives.

Causal state updates:
---
    accept deception               -> actor.conflict += 2
    reject deception               -> actor.honor += 2, actor.conflict -= 2
    use fake material              -> product.quality -= 1, product.brittle += 1
    use honest material            -> product.quality += 1, product.durable += 1
    confront deceiver              -> actor.conflict = 0, actor.honor += 3
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "queen"}
        male = {"boy", "father", "man", "king", "merchant"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def _r_deception_effect(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["accepted_deception"] >= THRESHOLD:
            for item in [e for e in world.entities.values() if e.owner == actor.id and e.kind == "product"]:
                if item.meters["fake"] >= THRESHOLD:
                    item.meters["quality"] -= 1
                    item.meters["brittle"] += 1
                    sig = ("ruin", item.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        out.append(f"The {item.label} grew weak and brittle.")
    return out


def _r_honor_resolve(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["conflict"] >= THRESHOLD and actor.memes["honor"] >= THRESHOLD * 3:
            sig = ("resolve", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["conflict"] = 0.0
                out.append(f"{actor.id} felt peace again.")
    return out


CAUSAL_RULES: list[tuple[str, str, Callable]] = [
    ("deception_effect", "physical", _r_deception_effect),
    ("honor_resolve", "social", _r_honor_resolve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for name, tag, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Storytelling verbs
# ---------------------------------------------------------------------------
def once_upon(world: World, hero: Entity, setting_phrase: str) -> None:
    world.say(f"Once upon a time, in {setting_phrase}, there lived a {hero.type} named {hero.id}.")


def show_craft(world: World, hero: Entity, craft: str) -> None:
    hero.memes["pride"] += 1
    world.say(f"{hero.id} was known far and wide for {craft}. The work brought joy to the whole valley.")


def merchant_arrives(world: World, hero: Entity, merchant: Entity, prize_label: str) -> None:
    world.say(f"One day, a {merchant.type} came to the valley. {merchant.pronoun().capitalize()} saw {hero.id}'s {prize_label} and smiled a sly smile.")


def offer_deception(world: World, hero: Entity, merchant: Entity, fake_material: str, craft_verb: str) -> None:
    world.say(f'"This span of cloth is fine," said the {merchant.type}, "but I can give you {fake_material} if you let me show you a secret."')
    world.say(f"{hero.id} was curious and agreed. The {merchant.type} took the good material and replaced it with {fake_material}.")
    world.say(f'"Now {craft_verb} faster," said the {merchant.type}, "and sell more!"')


def wise_one_warns(world: World, hero: Entity, wise: Entity, fake_material: str) -> None:
    world.say(f"But {hero.id}'s {wise.type} saw the deception.")
    world.say(f'"Child, this {fake_material} will not last," said the {wise.type}. "The {wise.type.removesuffix("mother") if "mother" in wise.type else "wise one"} is trying to deceive you."')


def conflict_rises(world: World, hero: Entity) -> None:
    hero.memes["conflict"] += 2
    world.say(f"{hero.id} felt torn. A deep conflict burned in {hero.pronoun('possessive')} heart.")


def choose_honor(world: World, hero: Entity, merchant: Entity, honest_material: str, craft_verb: str) -> None:
    hero.memes["honor"] += 2
    hero.memes["accepted_deception"] = 0.0
    world.say(f"In the end, {hero.id} chose to be a pro.")
    world.say(f"{hero.pronoun().capitalize()} returned the {honest_material}, wove only with true skill, and confronted the {merchant.type}.")
    world.say(f"The valley praised {hero.pronoun('possessive')} skill, and the {merchant.type} left ashamed.")
    world.say(f"{hero.id} learned that a true pro never deceives and that honest work spans a lifetime.")


# ---------------------------------------------------------------------------
# Tell the story
# ---------------------------------------------------------------------------
def tell(hero_name: str = "Elara", hero_type: str = "girl", wise_type: str = "grandmother",
         craft: str = "weaving beautiful blankets", craft_verb: str = "weave",
         honest_material: str = "soft wool", fake_material: str = "thin, brittle thread",
         prize_label: str = "blankets", setting_phrase: str = "a valley of golden hills",
         merchant_type: str = "merchant") -> World:

    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["young", "curious", "honest"]))
    wise = world.add(Entity(id="WiseOne", kind="character", type=wise_type,
                            traits=["wise", "kind"]))
    merchant = world.add(Entity(id="Merchant", kind="character", type=merchant_type,
                                traits=["trickster", "sly"]))
    product = world.add(Entity(id="Product", kind="product", type="craft",
                               label=prize_label, owner=hero.id,
                               phrase=f"her finest {prize_label}"))

    once_upon(world, hero, setting_phrase)
    show_craft(world, hero, craft)
    merchant_arrives(world, hero, merchant, prize_label)
    offer_deception(world, hero, merchant, fake_material, craft_verb)
    wise_one_warns(world, hero, wise, fake_material)
    conflict_rises(world, hero)
    choose_honor(world, hero, merchant, honest_material, craft_verb)

    world.facts.update(hero=hero, wise=wise, merchant=merchant, product=product,
                       craft=craft, craft_verb=craft_verb,
                       honest_material=honest_material, fake_material=fake_material,
                       prize_label=prize_label, setting_phrase=setting_phrase,
                       merchant_type=merchant_type)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HERO_TYPES = ["girl", "boy", "young weaver", "young blacksmith", "young farmer"]
WISE_TYPES = ["grandmother", "grandfather", "old teacher", "wise elder"]
CRAFTS = [
    ("weaving beautiful blankets", "weave", "soft wool", "thin, brittle thread", "blankets"),
    ("forging strong tools", "forge", "solid iron", "brittle, cracked metal", "tools"),
    ("baking hearty bread", "bake", "golden wheat flour", "chalky, tasteless powder", "loaves"),
]
SETTINGS = [
    "a valley of golden hills",
    "a forest of whispering pines",
    "a village by the sparkling sea",
    "a kingdom of rolling meadows",
]
MERCHANT_TYPES = ["merchant", "traveler", "peddler", "wandering trader"]

GIRL_NAMES = ["Elara", "Mira", "Sera", "Lina", "Tessa", "Nora", "Aria", "Lena", "Cora", "Fia"]
BOY_NAMES = ["Finn", "Kael", "Rune", "Bram", "Dane", "Liam", "Theo", "Eli", "Ivan", "Oren"]


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    wise_type: str
    craft_index: int
    setting_index: int
    merchant_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "deceive": [
        ("What does it mean to deceive someone?",
         "To deceive means to trick or lie to someone so they believe something that is not true."),
    ],
    "honest": [
        ("Why is honest work important?",
         "Honest work creates things that last and makes people proud. Tricks and shortcuts break easily."),
    ],
    "pro": [
        ("What is a pro?",
         "A pro is someone who is very skilled at their craft and always does good work, even when no one is watching."),
    ],
}
KNOWLEDGE_ORDER = ["deceive", "honest", "pro"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about a {f["hero"].type} named {f["hero"].id} who '
        f'learns that deception never wins.',
        f'Tell a story where a {f["merchant"].type} tries to deceive a young '
        f'crafts{("woman" if f["hero"].type in ("girl", "young weaver", "young farmer") else "man")} '
        f'and the wise {f["wise"].type} helps them choose honesty.',
        f'A short tale about the span of a life built on honest work, '
        f'featuring a pro who rejects deception.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, wise, merchant = f["hero"], f["wise"], f["merchant"]
    qa: list[QAItem] = [
        QAItem(
            question=f"What did {hero.id} love to make in {f['setting_phrase']}?",
            answer=f"{hero.pronoun().capitalize()} loved {f['craft']}. The whole valley knew about {hero.pronoun('possessive')} skill."
        ),
        QAItem(
            question=f"Who tried to deceive {hero.id} with {f['fake_material']}?",
            answer=f"A {merchant.type} came and offered {f['fake_material']} instead of {f['honest_material']}. {merchant.pronoun().capitalize()} wanted {hero.pronoun('object')} to work faster and sell more."
        ),
        QAItem(
            question=f"How did {wise.id} help {hero.id} see the deception?",
            answer=f"{wise.pronoun().capitalize()} warned that {f['fake_material']} would not last. The wise {wise.type} urged {hero.pronoun('object')} to be a true pro."
        ),
        QAItem(
            question=f"What did {hero.id} do after the conflict in {hero.pronoun('possessive')} heart?",
            answer=f"{hero.pronoun().capitalize()} chose honesty. {hero.pronoun().capitalize()} confronted the {merchant.type}, wove with {f['honest_material']}, and earned the valley's praise."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(HeroType, WiseType, CraftIdx, SettingIdx, MerchantType) :-
    hero_type(HeroType), wise_type(WiseType),
    craft_idx(CraftIdx), setting_idx(SettingIdx), merchant_type(MerchantType).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for ht in HERO_TYPES:
        lines.append(asp.fact("hero_type", ht))
    for wt in WISE_TYPES:
        lines.append(asp.fact("wise_type", wt))
    for i, _ in enumerate(CRAFTS):
        lines.append(asp.fact("craft_idx", i))
    for i, _ in enumerate(SETTINGS):
        lines.append(asp.fact("setting_idx", i))
    for mt in MERCHANT_TYPES:
        lines.append(asp.fact("merchant_type", mt))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    stories = asp_valid_stories()
    print(f"OK: clingo finds {len(stories)} valid story combinations.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale about deception, conflict, and honest work.")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--wise-type", choices=WISE_TYPES)
    ap.add_argument("--craft-idx", type=int, choices=range(len(CRAFTS)))
    ap.add_argument("--setting-idx", type=int, choices=range(len(SETTINGS)))
    ap.add_argument("--merchant-type", choices=MERCHANT_TYPES)
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
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    wise_type = args.wise_type or rng.choice(WISE_TYPES)
    craft_idx = args.craft_idx if args.craft_idx is not None else rng.choice(range(len(CRAFTS)))
    setting_idx = args.setting_idx if args.setting_idx is not None else rng.choice(range(len(SETTINGS)))
    merchant_type = args.merchant_type or rng.choice(MERCHANT_TYPES)
    names = GIRL_NAMES if hero_type in ("girl", "young weaver", "young farmer") else BOY_NAMES
    hero_name = args.hero_name or rng.choice(names)
    return StoryParams(hero_name=hero_name, hero_type=hero_type, wise_type=wise_type,
                       craft_index=craft_idx, setting_index=setting_idx,
                       merchant_type=merchant_type)


def generate(params: StoryParams) -> StorySample:
    craft = CRAFTS[params.craft_index]
    setting = SETTINGS[params.setting_index]
    world = tell(hero_name=params.hero_name, hero_type=params.hero_type,
                 wise_type=params.wise_type, craft=craft[0], craft_verb=craft[1],
                 honest_material=craft[2], fake_material=craft[3], prize_label=craft[4],
                 setting_phrase=setting, merchant_type=params.merchant_type)
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
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            print(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story combinations:")
        for s in stories:
            print(f"  {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
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
        header = f"### Fairy tale {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
