#!/usr/bin/env python3
"""
storyworlds/worlds/sequin_vile_magic_rhyme_sound_effects_superhero.py
=====================================================================

A small superhero storyworld with magic, rhyme, and sound effects.

Premise:
A young hero wears a sparkling sequin cape and wants to stop a vile troublemaker.
The hero uses magic words, a rhyming chant, and comic-book sound effects to
turn danger into a safe, bright ending.

The world is constraint-checked: the villain must create a real problem, the
hero must have a plausible power/tool response, and the ending must show what
changed.
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

MAGIC_EFFECTS = ("glow", "lift", "shield", "spark")
RHYME_CHANTS = (
    "shine and align",
    "flip the slip",
    "bright and right",
    "zip and flip",
)
SFX = ("Zap!", "Whirr!", "Pow!", "Bam!", "Shimmer!", "Zing!")

HERO_NAMES = ["Nova", "Ruby", "Milo", "Tessa", "Arlo", "Zara", "Finn", "Luna"]
SIDEKICK_NAMES = ["Pip", "Mimi", "Jax", "Bea", "Otto", "Nia"]
VILLAIN_NAMES = ["Grime Gloom", "Captain Sludge", "Moss Muck", "Duke Dull"]
PLACES = ["the city square", "the moonlit roof", "the bright museum", "the quiet park"]

SETTING_TONES = {
    "city square": "The city square gleamed with tall windows and busy steps.",
    "moonlit roof": "The moonlit roof sat high above the sleeping streets.",
    "bright museum": "The bright museum glittered with glass cases and polished floors.",
    "quiet park": "The quiet park rustled softly under the trees.",
}

MAGIC_TOOLS = [
    "star wand",
    "glow glove",
    "mirror ring",
    "light badge",
]

SOUND_ACTIONS = [
    "struck the air",
    "bounced off the wall",
    "spun in the lantern light",
    "crackled over the pavement",
]


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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class City:
    place: str
    tone: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "City":
        import copy as _copy
        c = City(self.place, self.tone)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    sidekick: str
    villain: str
    tool: str
    magic: str
    rhyme: str
    seed: Optional[int] = None


def _sound_for_effect(effect: str) -> str:
    return {"glow": "Shimmer!", "lift": "Whirr!", "shield": "Zap!", "spark": "Pow!"}.get(effect, "Zing!")


def _villain_problem(city: City, hero: Entity, villain: Entity) -> None:
    villain.memes["vile"] = villain.memes.get("vile", 0.0) + 1
    villain.meters["mess"] = villain.meters.get("mess", 0.0) + 1
    city.say(
        f"{villain.id} splashed vile slime across the path, and {hero.id}'s cape flickered with worry."
    )


def _predict_fix(city: City, hero: Entity, effect: str) -> bool:
    sim = city.copy()
    sim.get(hero.id).memes["hope"] = sim.get(hero.id).memes.get("hope", 0.0) + 1
    if effect not in MAGIC_EFFECTS:
        return False
    return True


def _hero_acts(city: City, hero: Entity, sidekick: Entity, villain: Entity, tool: Entity, effect: str, rhyme: str) -> None:
    sfx1 = _sound_for_effect(effect)
    city.say(
        f"{hero.id} raised the {tool.label}, and {sfx1} it began to {effect} with magic light."
    )
    city.say(
        f"{sidekick.id} clapped and called, \"{rhyme}!\" while the sound effects {random.choice(SOUND_ACTIONS)}."
    )
    hero.memes["brave"] = hero.memes.get("brave", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    villain.meters["mess"] = 0
    villain.memes["stopped"] = 1


def _resolution(city: City, hero: Entity, sidekick: Entity, villain: Entity, tool: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    city.say(
        f"The vile slime shrank into a tiny drip, the {tool.label} glowed kindly, and {hero.id} stood taller."
    )
    city.say(
        f"{sidekick.id} grinned, and together they watched the city shine again."
    )


def tell(place: str, hero_name: str, hero_type: str, sidekick_name: str, villain_name: str,
         tool_label: str, magic: str, rhyme: str) -> City:
    city = City(place=place, tone=SETTING_TONES.get(place, "The place waited for adventure."))
    hero = city.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["brave", "sparkly"]))
    sidekick = city.add(Entity(id=sidekick_name, kind="character", type="sidekick", traits=["quick", "cheerful"]))
    villain = city.add(Entity(id=villain_name, kind="character", type="villain", traits=["vile", "grumpy"]))
    tool = city.add(Entity(id="tool", type="tool", label=tool_label, phrase=f"a {tool_label}", owner=hero.id))

    city.say(f"{hero.id} was a small superhero who loved {tool.label} and a good rhyme.")
    city.say(f"{city.tone}")
    city.say(f"{hero.id} and {sidekick.id} kept watch for trouble, because {villain.id} always left a vile mess.")

    city.para()
    _villain_problem(city, hero, villain)
    if not _predict_fix(city, hero, magic):
        raise StoryError("The chosen magic cannot reasonably fix the villain's trouble.")

    city.say(f"{hero.id} whispered, \"{rhyme}.\"")
    _hero_acts(city, hero, sidekick, villain, tool, magic, rhyme)

    city.para()
    _resolution(city, hero, sidekick, villain, tool)

    hero.memes["resolved"] = 1
    city.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "villain": villain,
        "tool": tool,
        "place": place,
        "magic": magic,
        "rhyme": rhyme,
    }
    return city


def generation_prompts(city: City) -> list[str]:
    f = city.facts
    return [
        f'Write a short superhero story for a child that includes "{f["tool"].label}", magic, a rhyme, and a sound effect.',
        f"Tell a vivid story where {f['hero'].id} stops {f['villain'].id}'s vile trouble with {f['magic']} and a rhyme.",
        f'Write a simple superhero adventure set in {f["place"]} with a sparkling, sequin-like feeling and a happy ending.',
    ]


def story_qa(city: City) -> list[QAItem]:
    f = city.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    villain = f["villain"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"{hero.id} was the superhero, and {sidekick.id} helped with the plan.",
        ),
        QAItem(
            question=f"What did {villain.id} do that caused the problem?",
            answer=f"{villain.id} made a vile mess that covered the path and upset the hero.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the trouble?",
            answer=f"{hero.id} used the {tool.label}, magic, and a rhyme to stop the mess and make the place shine again.",
        ),
    ]


def world_qa(city: City) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses special courage, tools, or powers to protect others and solve problems.",
        ),
        QAItem(
            question="What does vile mean?",
            answer="Vile means very unpleasant, nasty, or disgusting.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are short words like Zap, Pow, or Whirr that help readers imagine action and excitement.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, which makes a chant or song fun to hear.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special kind of power that can make surprising things happen, like glowing, lifting, or shielding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(city: City) -> str:
    lines = ["--- trace ---"]
    for e in city.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for m in MAGIC_EFFECTS:
        lines.append(asp.fact("magic", m))
    for r in RHYME_CHANTS:
        lines.append(asp.fact("rhyme", r))
    for s in SFX:
        lines.append(asp.fact("sfx", s))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,M,R,S) :- place(P), magic(M), rhyme(R), sfx(S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, m, r, s) for p in PLACES for m in MAGIC_EFFECTS for r in RHYME_CHANTS for s in SFX}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl)[:10])
    if cl - py:
        print("  only in clingo:", sorted(cl - py)[:10])
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with magic, rhyme, and sound effects.")
    ap.add_argument("--place", choices=[p.replace("the ", "") for p in PLACES])
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--villain", choices=VILLAIN_NAMES)
    ap.add_argument("--tool", choices=MAGIC_TOOLS)
    ap.add_argument("--magic", choices=list(MAGIC_EFFECTS))
    ap.add_argument("--rhyme", choices=list(RHYME_CHANTS))
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
    place = args.place or rng.choice([p.replace("the ", "") for p in PLACES])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    tool = args.tool or rng.choice(MAGIC_TOOLS)
    magic = args.magic or rng.choice(MAGIC_EFFECTS)
    rhyme = args.rhyme or rng.choice(RHYME_CHANTS)
    return StoryParams(place=place, hero=hero, hero_type=hero_type, sidekick=sidekick, villain=villain, tool=tool, magic=magic, rhyme=rhyme)


def generate(params: StoryParams) -> StorySample:
    city = tell(
        place=params.place,
        hero_name=params.hero,
        hero_type=params.hero_type,
        sidekick_name=params.sidekick,
        villain_name=params.villain,
        tool_label=params.tool,
        magic=params.magic,
        rhyme=params.rhyme,
    )
    return StorySample(
        params=params,
        story=city.render(),
        prompts=generation_prompts(city),
        story_qa=story_qa(city),
        world_qa=world_qa(city),
        world=city,
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


CURATED = [
    StoryParams(place="city square", hero="Nova", hero_type="girl", sidekick="Pip", villain="Grime Gloom", tool="star wand", magic="shield", rhyme="shine and align"),
    StoryParams(place="moonlit roof", hero="Milo", hero_type="boy", sidekick="Jax", villain="Captain Sludge", tool="glow glove", magic="glow", rhyme="bright and right"),
    StoryParams(place="bright museum", hero="Zara", hero_type="girl", sidekick="Bea", villain="Moss Muck", tool="mirror ring", magic="spark", rhyme="flip the slip"),
    StoryParams(place="quiet park", hero="Arlo", hero_type="boy", sidekick="Mimi", villain="Duke Dull", tool="light badge", magic="lift", rhyme="zip and flip"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible combos:")
        for x in vals[:20]:
            print(" ", x)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
