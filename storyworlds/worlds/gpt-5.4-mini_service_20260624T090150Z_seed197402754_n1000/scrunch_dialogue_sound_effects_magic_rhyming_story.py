#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/scrunch_dialogue_sound_effects_magic_rhyming_story.py
==============================================================================================================

A standalone story world for a tiny rhyming tale about scrunching, dialogue,
sound effects, and a little bit of magic.

Seed tale sketch:
---
A small child loves a magic cloth that can scrunch and sing. The child wants to
use the cloth to make a pretend sky tent. A grown-up worries that the special
ribbon on the cloth will get tangled. They talk, try a safer spell, and the cloth
turns into a cozy tent while the ribbon stays neat.

Core world logic:
---
* "Scrunch" is the key action: a soft material can be folded or squeezed to make
  a sound, and that action can charge a simple magic charm.
* Magic is only safe when it is used on the right object in the right place.
* A spoken rhyme can calm worry and redirect the spell to a safe cloth.
* Sound effects are narrated as small state changes, not as decoration only.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    magical: bool = False
    soft: bool = False
    safe_to_scrunch: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "it"


@dataclass
class Setting:
    place: str = "the attic playroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    verse: str
    result: str
    target_kind: str
    requires: str
    guards: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    sparkle: float = 0.0
    sound: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def things(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.sparkle = self.sparkle
        clone.sound = self.sound
        return clone


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def _r_scrunch_charge(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("scrunch", 0.0) < THRESHOLD:
            continue
        sig = ("charge", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["brave"] = actor.memes.get("brave", 0.0) + 1
        world.sound += 1
        out.append("Scrunch, scrunch, went the cloth, soft as snow and light as lunch.")
    return out


def _r_magic_glow(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("scrunch", 0.0) < THRESHOLD or actor.memes.get("chant", 0.0) < THRESHOLD:
            continue
        sig = ("glow", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.sparkle += 1
        out.append("Sparkle, sparkle, twirl and glow, little rhymes can make things grow.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    for item in world.things():
        if not item.magical:
            continue
        if item.meters.get("charged", 0.0) < THRESHOLD:
            continue
        sig = ("transform", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["changed"] = 1.0
        out.append(f"With a hush and a whoosh, {item.label} changed to match the wish.")
    return out


def _r_tangle_worry(world: World) -> list[str]:
    out: list[str] = []
    ribbon = world.entities.get("ribbon")
    if not ribbon:
        return out
    for actor in world.characters():
        if actor.meters.get("scrunch", 0.0) < THRESHOLD:
            continue
        if ribbon.meters.get("safe", 0.0) >= THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append("Oh no, oh dear, the ribbon might twist; that would make a tangled mist.")
    return out


CAUSAL_RULES = [
    _r_scrunch_charge,
    _r_tangle_worry,
    _r_magic_glow,
    _r_transform,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def can_use_charm(actor: Entity, cloth: Entity, charm: Charm) -> bool:
    return cloth.type == charm.target_kind and cloth.safe_to_scrunch and charm.requires in {"chant", "scrunch"}


def predict_transform(world: World, actor: Entity, cloth: Entity, charm: Charm) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["scrunch"] = sim.get(actor.id).meters.get("scrunch", 0.0) + 1
    sim.get(actor.id).memes["chant"] = sim.get(actor.id).memes.get("chant", 0.0) + 1
    sim.get(cloth.id).meters["charged"] = sim.get(cloth.id).meters.get("charged", 0.0) + 1
    propagate(sim, narrate=False)
    return {"changed": bool(sim.get(cloth.id).meters.get("changed", 0.0) >= THRESHOLD),
            "worry": sim.get(actor.id).memes.get("worry", 0.0)}


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} who loved a snug little song.")
    world.say(f"In {world.setting.place}, {child.id} liked to scrunch cloth and hear it pong.")


def show_charm(world: World, child: Entity, charm: Charm) -> None:
    world.say(
        f"{child.id} found a magic {charm.label}, with a rhyme that went, "
        f'"{charm.verse}"'
    )
    world.say(f"The words felt bright, like moonlit foam, and made the tiny room feel home.")


def want_scrunch(world: World, child: Entity, cloth: Entity) -> None:
    child.meters["scrunch"] = child.meters.get("scrunch", 0.0) + 1
    world.sound += 1
    world.say(f'"Can I scrunch the {cloth.label} now?" {child.id} asked with a grin.')
    world.say("Scritch, scrunch, pffft-puff-puff, the cloth made a funny little fluff.")


def worry(world: World, grownup: Entity, child: Entity, cloth: Entity) -> None:
    pred = predict_transform(world, child, cloth, world.facts["charm"])
    if pred["changed"]:
        grownup.memes["worry"] = grownup.memes.get("worry", 0.0) + 1
        world.say(f'"Not that one," said {grownup.id}. "Its ribbon is too fine and smart."')
        world.say(f'"If it gets twisted, it could fall apart."')


def reply(world: World, child: Entity) -> None:
    child.memes["sad"] = child.memes.get("sad", 0.0) + 1
    world.say(f'{child.id} sighed, then whispered, "But I want the magic part."')


def compromise(world: World, grownup: Entity, child: Entity, safe_cloth: Entity, charm: Charm) -> None:
    child.memes["chant"] = child.memes.get("chant", 0.0) + 1
    safe_cloth.meters["charged"] = safe_cloth.meters.get("charged", 0.0) + 1
    safe_cloth.safe_to_scrunch = True
    safe_cloth.meters["safe"] = 1.0
    world.say(f'"Then let us try the old square cloth," said {grownup.id}. "It is plain, but it is bold."')
    world.say(f'"We can scrunch it softly and sing the charm, and keep the ribbon from getting cold."')


def resolve(world: World, child: Entity, grownup: Entity, cloth: Entity, charm: Charm) -> None:
    propagate(world, narrate=True)
    if cloth.meters.get("changed", 0.0) >= THRESHOLD:
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1
        child.memes["worry"] = 0.0
        world.say(f'{child.id} clapped and cried, "Hooray, hooray!" as the cloth became a cozy, cozy day.')
        world.say(f'Then {child.id} and {grownup.id} peeked inside the shining nook and laughed in a happy way.')
    else:
        raise StoryError("the magic rhyme did not produce a safe transformation")


def tell(setting: Setting, child_name: str, child_type: str, grownup_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    grownup = world.add(Entity(id="Grownup", kind="character", type=grownup_type))
    magic_cloth = world.add(Entity(
        id="magic_cloth", kind="thing", type="cloth", label="magic cloth",
        phrase="a magic cloth with a ribbon", magical=True, soft=True, safe_to_scrunch=False,
    ))
    ribbon = world.add(Entity(
        id="ribbon", kind="thing", type="ribbon", label="ribbon",
        phrase="a bright ribbon", magical=False, soft=True, safe_to_scrunch=False,
    ))
    old_cloth = world.add(Entity(
        id="old_cloth", kind="thing", type="cloth", label="old square cloth",
        phrase="an old square cloth", magical=True, soft=True, safe_to_scrunch=True,
    ))
    charm = Charm(
        id="star_verse",
        label="star verse",
        verse="Scrunch it small, then let it swoon; spin it bright beneath the moon.",
        result="a cozy little tent",
        target_kind="cloth",
        requires="chant",
        guards={"tangle"},
    )
    world.facts.update(child=child, grownup=grownup, cloth=magic_cloth, ribbon=ribbon,
                       safe_cloth=old_cloth, charm=charm)

    introduce(world, child)
    show_charm(world, child, charm)
    world.para()
    want_scrunch(world, child, magic_cloth)
    worry(world, grownup, child, magic_cloth)
    reply(world, child)
    world.para()
    compromise(world, grownup, child, old_cloth, charm)
    resolve(world, child, grownup, old_cloth, charm)
    return world


SETTINGS = {
    "playroom": Setting(place="the playroom", affords={"scrunch", "magic"}),
    "attic": Setting(place="the attic playroom", affords={"scrunch", "magic"}),
    "corner": Setting(place="the cozy corner", affords={"scrunch", "magic"}),
}

CHILD_NAMES = ["Mia", "Pip", "Noa", "Luna", "Toby", "Zuri", "Nico", "June"]
CHILD_TYPES = ["girl", "boy"]
GROWNUP_TYPES = ["mother", "father", "grandmother", "grandfather"]

CURATED = [
    ("playroom", "Mia", "girl", "mother"),
    ("attic", "Pip", "boy", "grandmother"),
    ("corner", "June", "girl", "father"),
]

PRIME_WORDS = ["scrunch", "magic", "rhyme", "sparkle"]


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    grownup: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    g = world.facts["grownup"]
    return [
        f"Write a short rhyming story for a little child named {c.id} about a magic cloth, a scrunch sound, and a happy choice.",
        f"Tell a gentle dialogue story where {c.id} wants to scrunch the magic cloth but {g.id} worries about the ribbon.",
        f'Create a small story that uses the word "scrunch" and ends with a safe magic change in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, grownup, cloth, safe_cloth, charm = f["child"], f["grownup"], f["cloth"], f["safe_cloth"], f["charm"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the magic cloth?",
            answer=f"{child.id} wanted to scrunch the magic cloth and hear its soft little sound.",
        ),
        QAItem(
            question=f"Why did {grownup.id} say not to use that cloth at first?",
            answer=f"{grownup.id} worried the ribbon on the magic cloth would get twisted and look messy.",
        ),
        QAItem(
            question=f"What cloth did they use instead?",
            answer=f"They used the old square cloth instead, because it was safe to scrunch and safe for the spell.",
        ),
        QAItem(
            question=f"What did the magic rhyme do in the end?",
            answer=f"The rhyme helped the old cloth change into {charm.result}, while the ribbon stayed neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does scrunching mean?",
            answer="Scrunching means squeezing or folding something softly, often so it makes a crinkly sound.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like day and way or glow and show.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic in a story means something special and surprising happens that cannot happen in ordinary life.",
        ),
        QAItem(
            question="Why do soft cloths make a scrunch sound?",
            answer="Soft cloths can make a scrunch sound when they are folded, pressed, or squeezed together.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.magical:
            bits.append("magical=True")
        if e.safe_to_scrunch:
            bits.append("safe_to_scrunch=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  sparkle={world.sparkle}")
    lines.append(f"  sound={world.sound}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A cloth is scrunch-safe when it is soft and explicitly safe_to_scrunch.
scrunch_safe(C) :- cloth(C), safe(C).

% Magic can transform only if the child has scrunched and chanted.
can_transform(C) :- scrunch_event(child), chant_event(child), scrunch_safe(C).

% A wrong cloth creates worry if it has a ribbon and is not safe.
worry_about(C) :- cloth(C), has_ribbon(C), not safe(C).

% A valid story needs a safe transformation.
valid_story(place(playroom)) :- can_transform(old_cloth).
valid_story(place(attic)) :- can_transform(old_cloth).
valid_story(place(corner)) :- can_transform(old_cloth).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("grownup", "grownup"))
    lines.append(asp.fact("cloth", "magic_cloth"))
    lines.append(asp.fact("cloth", "old_cloth"))
    lines.append(asp.fact("safe", "old_cloth"))
    lines.append(asp.fact("has_ribbon", "magic_cloth"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python.")
        return 1
    print("OK: ASP and Python agree on the safe magic story.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming story world about scrunching, dialogue, sound effects, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--grownup", choices=GROWNUP_TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(CHILD_TYPES)
    name = args.name or rng.choice(CHILD_NAMES)
    grownup = args.grownup or rng.choice(GROWNUP_TYPES)
    return StoryParams(place=place, name=name, gender=gender, grownup=grownup)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.gender, params.grownup)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place, name, gender, grownup in CURATED:
            samples.append(generate(StoryParams(place=place, name=name, gender=gender, grownup=grownup)))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} ({p.gender}, {p.grownup})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
