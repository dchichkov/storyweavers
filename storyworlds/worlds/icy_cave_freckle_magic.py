#!/usr/bin/env python3
"""
storyworlds/worlds/icy_cave_freckle_magic.py
============================================

A standalone storyworld from the seed:

    Words: icy cave, freckle
    Features: Sound Effects, Magic
    Style: Fairy Tale

Source tale written for this world
----------------------------------
Once upon a time, a brave child named Mira lived below an icy cave where the
winter bell had gone silent. Mira had a tiny silver freckle on her cheek. Her
grandmother said it was a truth-spark: it only glowed when Mira used a clear,
honest sound.

One frosty morning, the village stream froze solid. Mira wanted to run into the
icy cave and find the bell, but Grandmother stopped her. "If you make the wrong
noise in there, the ice will either swallow the sound or crack," she said. She
asked Mira to test a small sound first.

Mira chose the little brass bell. Ting! The sound rang clear against the blue
walls. Her freckle shimmered, the frozen door softened, and the winter bell
answered with a deep Bong! Warmth flowed back down the hill, and the stream
began to sparkle again.

Model shape
-----------
The cave, sound, freckle, and frozen wonder are physical carriers with meters
and emotional/magic memes. A clear resonant sound embeds magic in the freckle;
that state unlocks the obstacle and restores the village wonder. The model
refuses weak variants: a muffled sound will not carry in the cave, and a harsh
loud sound would crack a fragile cave instead of solving the problem.
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
    traits: list[str] = field(default_factory=list)
    carrier: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Cave:
    id: str
    name: str
    look: str
    amplifies: set[str]
    fragile: int
    treasure_room: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sound:
    id: str
    label: str
    action: str
    effect: str
    quality: str
    volume: int
    clear: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Mark:
    id: str
    label: str
    phrase: str
    truth_magic: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Wonder:
    id: str
    label: str
    frozen_problem: str
    restored_image: str
    answer_sound: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_freckle_glows(world: World) -> list[str]:
    sound = world.get("sound")
    mark = world.get("mark")
    cave = world.get("cave")
    if sound.meters["clear_ring"] < THRESHOLD or mark.memes["truth"] < THRESHOLD:
        return []
    if sound.carrier not in cave.traits:
        return []
    sig = ("glow", mark.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mark.memes["magic"] += 1
    mark.meters["glow"] += 1
    return ["__glow__"]


def _r_ice_cracks(world: World) -> list[str]:
    sound = world.get("sound")
    cave = world.get("cave")
    if sound.meters["vibration"] <= cave.meters["fragility"]:
        return []
    sig = ("crack", cave.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cave.meters["cracked"] += 1
    world.get("hero").memes["fear"] += 1
    return ["__crack__"]


def _r_unlocks(world: World) -> list[str]:
    mark = world.get("mark")
    cave = world.get("cave")
    door = world.get("door")
    if mark.memes["magic"] < THRESHOLD or cave.meters["cracked"] >= THRESHOLD:
        return []
    sig = ("unlock", door.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    door.meters["frozen"] = 0.0
    door.meters["open"] += 1
    return ["__unlock__"]


def _r_restores(world: World) -> list[str]:
    door = world.get("door")
    wonder = world.get("wonder")
    if door.meters["open"] < THRESHOLD:
        return []
    sig = ("restore", wonder.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wonder.meters["frozen"] = 0.0
    wonder.memes["awake"] += 1
    world.get("hero").memes["joy"] += 1
    return ["__restore__"]


CAUSAL_RULES = [
    Rule("freckle_glows", "magic", _r_freckle_glows),
    Rule("ice_cracks", "physical", _r_ice_cracks),
    Rule("unlocks", "magic", _r_unlocks),
    Rule("restores", "physical", _r_restores),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def is_resonant(cave: Cave, sound: Sound) -> bool:
    return sound.clear and sound.quality in cave.amplifies


def is_safe(cave: Cave, sound: Sound) -> bool:
    return sound.volume <= cave.fragile


def can_awaken(cave: Cave, sound: Sound, mark: Mark) -> bool:
    return mark.truth_magic and is_resonant(cave, sound) and is_safe(cave, sound)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for cave_id, cave in CAVES.items():
        for sound_id, sound in SOUNDS.items():
            for mark_id, mark in MARKS.items():
                for wonder_id in WONDERS:
                    if can_awaken(cave, sound, mark):
                        out.append((cave_id, sound_id, mark_id, wonder_id))
    return sorted(out)


def outcome_of(params: "StoryParams") -> str:
    cave, sound, mark = CAVES[params.cave], SOUNDS[params.sound], MARKS[params.mark]
    if not is_safe(cave, sound):
        return "cracked"
    if can_awaken(cave, sound, mark):
        return "restored"
    return "silent"


def make_sound(world: World, cave: Cave, sound: Sound, mark: Mark) -> None:
    snd = world.get("sound")
    mk = world.get("mark")
    cv = world.get("cave")
    snd.carrier = sound.quality
    snd.meters["vibration"] += sound.volume
    if sound.clear:
        snd.meters["clear_ring"] += 1
    if mark.truth_magic:
        mk.memes["truth"] += 1
    cv.meters["fragility"] = cave.fragile
    propagate(world)


def predict(world: World, cave: Cave, sound: Sound, mark: Mark) -> dict:
    sim = world.copy()
    make_sound(sim, cave, sound, mark)
    return {
        "glows": sim.get("mark").meters["glow"] >= THRESHOLD,
        "cracks": sim.get("cave").meters["cracked"] >= THRESHOLD,
        "opens": sim.get("door").meters["open"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, cave: Cave, mark: Mark, wonder: Wonder) -> None:
    world.say(
        f"Once upon a time, {hero.label} lived below {cave.name}, where "
        f"{wonder.frozen_problem}."
    )
    world.say(
        f"On {hero.pronoun('possessive')} cheek was {mark.phrase}. "
        f"Grandmother called it a truth-spark, a little magic that listened "
        f"only to honest sounds."
    )


def warning(world: World, hero: Entity, cave: Cave, sound: Sound, mark: Mark) -> None:
    pred = predict(world, cave, sound, mark)
    world.facts["prediction"] = pred
    world.say(
        f"One frosty morning, {hero.label} wanted to hurry into the icy cave, "
        f"but Grandmother held up her mitten."
    )
    if pred["opens"]:
        world.say(
            f'"A sound like {sound.label} may carry," she said, '
            f'"but try it gently and tell the cave the truth."'
        )
    elif pred["cracks"]:
        world.say(
            f'"That sound is too rough for old ice," she warned. '
            f'"It could crack the roof before any magic wakes."'
        )
    else:
        world.say(
            f'"That sound will be swallowed by the snow," she warned. '
            f'"The freckle cannot glow unless the cave hears clearly."'
        )


def attempt(world: World, hero: Entity, cave: Cave, sound: Sound, mark: Mark) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"{hero.label} stepped into {cave.treasure_room}. "
        f"{sound.action.format(name=hero.label)} {sound.effect}"
    )
    make_sound(world, cave, sound, mark)
    mk = world.get("mark")
    cv = world.get("cave")
    if mk.meters["glow"] >= THRESHOLD:
        world.say(
            f"The {mark.label} shimmered on {hero.pronoun('possessive')} "
            f"cheek, and the cave answered with a soft blue gleam."
        )
    if cv.meters["cracked"] >= THRESHOLD:
        world.say(
            "Crack! A thin white line ran across the ceiling, and the magic "
            "hid itself deep in the ice."
        )


def finish(world: World, hero: Entity, wonder: Wonder) -> None:
    door = world.get("door")
    w = world.get("wonder")
    if door.meters["open"] >= THRESHOLD and w.memes["awake"] >= THRESHOLD:
        image = wonder.restored_image[0].upper() + wonder.restored_image[1:]
        world.say(
            f"The frozen door softened. From beyond it came {wonder.answer_sound} "
            f"{image}."
        )
        world.say(
            f"{hero.label} walked home with the glow fading to a happy sparkle. "
            "From then on, the village remembered that magic works best when "
            "a brave heart makes a careful sound."
        )
    elif world.get("cave").meters["cracked"] >= THRESHOLD:
        world.say(
            f"{hero.label} backed out slowly and promised to ask for a gentler sound. "
            "The cave stayed closed, but the lesson rang clear."
        )
    else:
        world.say(
            f"The cave stayed silent. {hero.label} listened to the quiet and learned "
            "that not every noise can carry a true wish."
        )


def tell(cave: Cave, sound: Sound, mark: Mark, wonder: Wonder,
         name: str, gender: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity("hero", "character", gender, name, [trait]))
    world.add(Entity("cave", "place", "cave", cave.name, list(cave.amplifies)))
    world.add(Entity("sound", "thing", "sound", sound.label))
    world.add(Entity("mark", "thing", "freckle", mark.label))
    door = world.add(Entity("door", "thing", "ice door", "the frozen door"))
    door.meters["frozen"] = 1
    w = world.add(Entity("wonder", "thing", wonder.id, wonder.label))
    w.meters["frozen"] = 1

    introduce(world, hero, cave, mark, wonder)
    world.para()
    warning(world, hero, cave, sound, mark)
    attempt(world, hero, cave, sound, mark)
    world.para()
    finish(world, hero, wonder)
    world.facts.update(hero=hero, cave=cave, sound=sound, mark=mark, wonder=wonder,
                       outcome=outcome_of(StoryParams(cave.id, sound.id, mark.id,
                                                      wonder.id, name, gender, trait)))
    return world


CAVES = {
    "icy_cave": Cave("icy_cave", "an icy cave", "blue walls glittered like glass",
                     {"bell", "voice"}, 2, "the blue cave hall",
                     {"icy_cave", "echo"}),
    "frost_grotto": Cave("frost_grotto", "the frost grotto",
                         "icicles hung like tiny chandeliers",
                         {"bell", "whistle"}, 2, "the glittering grotto",
                         {"icy_cave", "icicle"}),
    "snow_tunnel": Cave("snow_tunnel", "the snow tunnel",
                        "packed snow made every sound soft",
                        {"voice"}, 1, "the narrow snow tunnel",
                        {"snow", "echo"}),
}

SOUNDS = {
    "brass_bell": Sound("brass_bell", "a little brass bell", "Ting! {name} rang the bell.",
                        "The note flew bright and round through the ice.",
                        "bell", 1, True, {"bell", "sound"}),
    "true_hum": Sound("true_hum", "a true humming song", "Hmmm. {name} hummed one steady note.",
                      "The sound warmed the air without pushing it.",
                      "voice", 1, True, {"voice", "sound"}),
    "silver_whistle": Sound("silver_whistle", "a silver whistle",
                            "Phee-ee! {name} blew the whistle softly.",
                            "The note slipped between the icicles.",
                            "whistle", 1, True, {"whistle", "sound"}),
    "wooden_drum": Sound("wooden_drum", "a wooden drum", "Boom! {name} struck the drum.",
                         "The heavy beat shook snow from the roof.",
                         "drum", 3, True, {"drum", "sound"}),
    "wool_pillow": Sound("wool_pillow", "a wool pillow", "Poof. {name} squeezed the pillow.",
                         "The tiny sound fell flat in the snow.",
                         "muffle", 0, False, {"quiet"}),
}

MARKS = {
    "silver_freckle": Mark("silver_freckle", "silver freckle",
                           "a tiny silver freckle", True, {"freckle", "magic"}),
    "gold_freckle": Mark("gold_freckle", "gold freckle",
                         "a little gold freckle shaped like a star", True,
                         {"freckle", "magic"}),
    "paint_dot": Mark("paint_dot", "paint dot",
                      "a dot of silver paint that only looked magical", False,
                      {"freckle"}),
}

WONDERS = {
    "winter_bell": Wonder("winter_bell", "the winter bell",
                          "the winter bell had gone silent and the stream froze solid",
                          "warmth flowed back down the hill until the village stream sparkled",
                          "a deep Bong!", {"bell", "winter"}),
    "moon_lantern": Wonder("moon_lantern", "the moon lantern",
                           "the moon lantern slept and every path turned dark",
                           "moonlight poured over the path like milk",
                           "a bright Chime!", {"lantern", "moon"}),
    "star_seed": Wonder("star_seed", "the star seed",
                        "the star seed froze and the garden forgot how to sprout",
                        "green shoots pricked through the snow",
                        "a tiny Ping!", {"seed", "winter"}),
}

GIRL_NAMES = ["Mira", "Lina", "Ava", "Nora", "Elsa"]
BOY_NAMES = ["Toma", "Finn", "Leo", "Noah", "Eli"]
TRAITS = ["brave", "curious", "gentle", "patient"]


@dataclass
class StoryParams:
    cave: str
    sound: str
    mark: str
    wonder: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "icy_cave": [("What is an icy cave?",
                  "An icy cave is a cave where water has frozen into ice. Sounds can echo there because the hard walls bounce the sound back.")],
    "freckle": [("What is a freckle?",
                 "A freckle is a small spot on someone's skin. In this fairy tale, the freckle is magical because the story gives it that power.")],
    "magic": [("How does magic work in fairy tales?",
               "Fairy-tale magic follows special story rules. In this story it only works when a clear sound carries an honest wish.")],
    "sound": [("What makes a sound echo?",
               "A sound echoes when it bounces off a hard surface and comes back to your ears.")],
    "bell": [("Why do bells ring clearly?",
              "Bells are shaped so they vibrate evenly when struck, which makes a clear ringing sound.")],
    "voice": [("Can a voice make echoes?",
               "Yes. A voice can echo when someone hums or calls in a place with hard walls, like a cave.")],
    "whistle": [("What is a whistle?",
                 "A whistle is a small tool that makes a high clear sound when air moves through it.")],
}
KNOWLEDGE_ORDER = ["icy_cave", "freckle", "magic", "sound", "bell", "voice", "whistle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fairy tale for young children that includes the words "icy cave" and "freckle", with sound effects and magic.',
        f"Tell a story where {f['hero'].label} uses {f['sound'].label} in {f['cave'].name} and a magical {f['mark'].label} helps restore {f['wonder'].label}.",
        "Write a gentle adventure where the right sound matters more than being loud.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, cave, sound, mark, wonder = f["hero"], f["cave"], f["sound"], f["mark"], f["wonder"]
    pred = f.get("prediction", {})
    opened = "would open the way" if pred.get("opens") else "would not open the way"
    cracked = "would crack the cave" if pred.get("cracks") else "would not crack the cave"
    return [
        ("Who is the story about?",
         f"The story is about {hero.label}, a {hero.traits[0]} {hero.type} with {mark.phrase}."),
        ("What problem made the adventure happen?",
         f"{wonder.frozen_problem.capitalize()}. That problem pulled {hero.label} toward {cave.name}."),
        ("What sound did the child choose?",
         f"{hero.label} chose {sound.label}. The sound mattered because the cave's magic needed something clear and careful."),
        ("Why did Grandmother warn the child?",
         f"Grandmother warned {hero.label} because the cave would only answer a sound that carried clearly. In her prediction, the sound {opened} and {cracked}, so it was worth trying carefully."),
        ("How did the story end?",
         f"The final image was that {wonder.restored_image}. That change proves the magic became embedded in the freckle and then in the world."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["cave"].tags) | set(f["sound"].tags) | set(f["mark"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("icy_cave", "brass_bell", "silver_freckle", "winter_bell",
                "Mira", "girl", "brave"),
    StoryParams("icy_cave", "true_hum", "gold_freckle", "moon_lantern",
                "Finn", "boy", "gentle"),
    StoryParams("frost_grotto", "silver_whistle", "silver_freckle", "star_seed",
                "Nora", "girl", "patient"),
]


def explain_rejection(cave: Cave, sound: Sound, mark: Mark) -> str:
    if not mark.truth_magic:
        return f"(No story: {mark.phrase} is not a true magic freckle, so the sound has no carrier for the spell.)"
    if not is_resonant(cave, sound):
        return f"(No story: {sound.label} does not carry clearly in {cave.name}; the cave would swallow the sound.)"
    if not is_safe(cave, sound):
        return f"(No story: {sound.label} is too loud for {cave.name}; it would crack the ice instead of waking the magic.)"
    return "(No story: the magic rule cannot awaken this combination.)"


ASP_RULES = r"""
resonant(C,S) :- amplifies(C,Q), quality(S,Q), clear(S).
safe(C,S) :- cave(C), sound(S), volume(S,V), fragile(C,F), V <= F.
valid(C,S,M,W) :- cave(C), sound(S), mark(M), wonder(W), truth_magic(M), resonant(C,S), safe(C,S).

outcome(cracked) :- chosen_cave(C), chosen_sound(S), volume(S,V), fragile(C,F), V > F.
outcome(restored) :- chosen_cave(C), chosen_sound(S), chosen_mark(M),
                     truth_magic(M), resonant(C,S), safe(C,S).
outcome(silent) :- not outcome(cracked), not outcome(restored).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid, cave in CAVES.items():
        lines.append(asp.fact("cave", cid))
        lines.append(asp.fact("fragile", cid, cave.fragile))
        for q in sorted(cave.amplifies):
            lines.append(asp.fact("amplifies", cid, q))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("quality", sid, sound.quality))
        lines.append(asp.fact("volume", sid, sound.volume))
        if sound.clear:
            lines.append(asp.fact("clear", sid))
    for mid, mark in MARKS.items():
        lines.append(asp.fact("mark", mid))
        if mark.truth_magic:
            lines.append(asp.fact("truth_magic", mid))
    for wid in WONDERS:
        lines.append(asp.fact("wonder", wid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_cave", params.cave),
        asp.fact("chosen_sound", params.sound),
        asp.fact("chosen_mark", params.mark),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: clingo gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("  only clingo:", sorted(cset - pset))
        print("  only python:", sorted(pset - cset))
    cases = list(CURATED)
    parser = build_parser()
    for seed in range(150):
        cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome cases differ.")
    return rc


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: an icy cave, a freckle, sound effects, and fairy-tale magic.")
    ap.add_argument("--cave", choices=CAVES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--mark", choices=MARKS)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.cave and args.sound and args.mark:
        cave, sound, mark = CAVES[args.cave], SOUNDS[args.sound], MARKS[args.mark]
        if not can_awaken(cave, sound, mark):
            raise StoryError(explain_rejection(cave, sound, mark))
    combos = [c for c in valid_combos()
              if (args.cave is None or c[0] == args.cave)
              and (args.sound is None or c[1] == args.sound)
              and (args.mark is None or c[2] == args.mark)
              and (args.wonder is None or c[3] == args.wonder)]
    if not combos:
        raise StoryError("(No valid icy-cave story matches the given options.)")
    cave, sound, mark, wonder = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(cave, sound, mark, wonder, name, gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(CAVES[params.cave], SOUNDS[params.sound], MARKS[params.mark],
                 WONDERS[params.wonder], params.name, params.gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cave, sound, mark, wonder) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:15}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.sound} in {p.cave} ({p.wonder})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
