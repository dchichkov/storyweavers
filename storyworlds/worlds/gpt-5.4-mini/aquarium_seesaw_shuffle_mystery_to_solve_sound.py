#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/aquarium_seesaw_shuffle_mystery_to_solve_sound.py
===================================================================================

A standalone storyworld for a pirate-style quest at an aquarium playground.

Premise
-------
Two children turn an aquarium visit into a pirate quest. They hear a strange
shuffle and a funny clank from a nearby seesaw, then discover that a small
mystery has a simple cause: a tangled ribbon and a toy key that must be freed
before the fish scare can grow. A grown-up helper and a safe sound effect kit
turn the scene from spooky to triumphant.

This world keeps the classical tiny-story structure:
- a clear setting and quest,
- a mystery to solve,
- sound effects that are driven by state,
- a turn where the problem is explained and fixed,
- an ending image proving what changed.

It also includes:
- typed entities with meters and memes,
- a Python reasonableness gate,
- inline ASP rules as a twin,
- three Q&A sets grounded in simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/aquarium_seesaw_shuffle_mystery_to_solve_sound.py
    python storyworlds/worlds/gpt-5.4-mini/aquarium_seesaw_shuffle_mystery_to_solve_sound.py --all
    python storyworlds/worlds/gpt-5.4-mini/aquarium_seesaw_shuffle_mystery_to_solve_sound.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/aquarium_seesaw_shuffle_mystery_to_solve_sound.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    theme_line: str
    dark_spot: str
    quest: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    sound: str
    clue: str
    cause: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundKit:
    id: str
    label: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    if world.get("mystery").meters["spooky"] >= THRESHOLD and "room" in world.entities:
        sig = ("spook",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("room").meters["tension"] += 1
            for name in ("child1", "child2"):
                world.get(name).memes["fear"] += 1
            out.append("__spook__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.get("mystery").meters["solved"] >= THRESHOLD:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("room").meters["tension"] = 0.0
            for name in ("child1", "child2"):
                world.get(name).memes["joy"] += 1
                world.get(name).memes["relief"] += 1
            out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook), Rule("reveal", "social", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mystery_at_risk(setting: Setting, mystery: Mystery) -> bool:
    return "aquarium" in setting.tags and "shuffle" in mystery.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return "(No story: this setup must include an aquarium shuffle mystery, with a sound that can be explained and solved.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it is too weak in common sense (sense={r.sense} < {SENSE_MIN}). Try: {good}.)"


def predict_mystery(world: World) -> dict:
    sim = world.copy()
    _start_mystery(sim, narrate=False)
    return {"spooky": sim.get("mystery").meters["spooky"], "tension": sim.get("room").meters["tension"]}


def _start_mystery(world: World, narrate: bool = True) -> None:
    m = world.get("mystery")
    m.meters["spooky"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, setting: Setting, a: Entity, b: Entity) -> None:
    a.memes["bravery"] = 6
    b.memes["curiosity"] = 5
    world.say(f"On a bright day, {a.id} and {b.id} turned {setting.place} into a pirate quest. {setting.theme_line}")
    world.say(f'"Captain {a.id}!" {a.id} shouted. "Scout {b.id}!" {b.id} replied. "Our quest is to find {setting.quest}!"')


def hear_sound(world: World, setting: Setting, mystery: Mystery) -> None:
    world.say(f"But near the {setting.dark_spot}, they heard a strange shuffle. {mystery.sound} came again, soft as a secret.")
    world.say(f'{world.get("child2").id} peered ahead. "Did you hear that sound?" {world.get("child2").pronoun()} asked.')


def wonder(world: World, child: Entity, mystery: Mystery) -> None:
    world.say(f'{child.id} tilted {child.pronoun("possessive")} head. "That sound belongs to the mystery," {child.pronoun()} said.')


def warn(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    pred = predict_mystery(world)
    world.facts["predicted"] = pred
    world.say(f'{child.id} bit {child.pronoun("possessive")} lip. "{helper.label_word.capitalize()} said to stay careful," {child.pronoun()} whispered. "Something is tangled near the tank."')


def investigate(world: World, child1: Entity, child2: Entity, mystery: Mystery) -> None:
    child1.memes["curiosity"] += 1
    child2.memes["curiosity"] += 1
    world.say(f'The two children shuffled closer, making a soft shuffle of their own.')


def reveal(world: World, mystery: Mystery, setting: Setting) -> None:
    mystery.meters["solved"] += 1
    world.say(f'At last, the clue made sense: {mystery.cause}. {mystery.reveal}')


def fix(world: World, helper: Entity, response: Response, kit: SoundKit) -> None:
    world.say(f'{helper.label_word.capitalize()} came over with {kit.label}. In a flash, {helper.pronoun()} {response.text}.')
    world.say(f'The aquarium stayed calm, and the shuffle sound vanished.')


def ending(world: World, setting: Setting, a: Entity, b: Entity, quest_item: str) -> None:
    world.say(f'After that, the pirate quest could go on. {a.id} and {b.id} smiled, and the aquarium shone clear behind them.')
    world.say(f'This time, their treasure was not a coin at all -- it was {quest_item}, solved and safe.')


def rescue_fail(world: World, response: Response, mystery: Mystery) -> None:
    world.say(f'But {response.fail}. The mystery stayed noisy for a moment longer.')


def tell(setting: Setting, mystery: Mystery, kit: SoundKit, response: Response,
         child1: str = "Mina", child1_gender: str = "girl",
         child2: str = "Toby", child2_gender: str = "boy",
         helper_type: str = "mother", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="captain"))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="scout"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    myst = world.add(Entity(id="mystery", type="mystery", label=mystery.id))
    setup(world, setting, a, b)
    world.para()
    hear_sound(world, setting, mystery)
    wonder(world, b, mystery)
    warn(world, b, helper, mystery)
    investigate(world, a, b, mystery)
    world.para()
    _start_mystery(world)
    if is_contained(response, delay):
        world.para()
        reveal(world, mystery, setting)
        fix(world, helper, response, kit)
        ending(world, setting, a, b, setting.quest)
    else:
        world.para()
        rescue_fail(world, response, mystery)
        world.get("mystery").meters["solved"] += 1
        world.say("Then the helper solved it the simple way, and the children cheered.")
        ending(world, setting, a, b, setting.quest)
    world.facts.update(child1=a, child2=b, helper=helper, room=room, mystery=myst, setting=setting, kit=kit, response=response, delay=delay, outcome="contained")
    return world


SETTINGS = {
    "aquarium": Setting("aquarium", "the aquarium", "The glass tunnel glimmered with blue light, and the fish swished like silver arrows.", "the shell path beside the tank", "the pearl key", tags={"aquarium"}),
    "dock": Setting("dock", "the dock", "The dock boards creaked over the water, and the ropes swung like sleeping snakes.", "the rope pile", "the lost map", tags={"dock"}),
    "harbor": Setting("harbor", "the harbor", "The boats bobbed gently, and gulls cried overhead like tiny trumpets.", "the pier corner", "the captain's whistle", tags={"harbor"}),
}

MYSTERIES = {
    "shuffle": Mystery("shuffle", "A shuffle-shuffle sound!", "a clue hidden near the seesaw", "a ribbon caught under the seesaw seat", "The ribbon was caught on a toy key, and that made the odd sound.", tags={"shuffle", "sound", "mystery"}),
    "clank": Mystery("clank", "Clank-clink!", "a clue behind the crate", "a loose shell in a tin cup", "The tin cup had rolled under a crate and tapped each time it moved.", tags={"sound", "mystery"}),
}

SOUND_KITS = {
    "shaker": SoundKit("shaker", "a little sound kit", "shook a wooden shaker and tapped a drum", tags={"sound"}),
    "bell": SoundKit("bell", "a bell kit", "rang a bell and shook tiny beads", tags={"sound"}),
}

RESPONSES = {
    "calm": Response("calm", 3, 3, "checked the ribbon, lifted the toy key free, and showed the children the simple trick behind the sound", "looked around, but could not calm the mystery", "checked the ribbon, lifted the toy key free, and showed the children the simple trick behind the sound", tags={"solve"}),
    "tap": Response("tap", 2, 2, "tapped the loose piece into place and made the sound stop", "tapped at the wrong spot, and the sound kept going", "tapped the loose piece into place and made the sound stop", tags={"solve"}),
    "water_bottle": Response("water_bottle", 1, 1, "poured water everywhere", "poured water everywhere, but that did not solve the mystery", "poured water everywhere", tags={"weak"}),
}

CURATED = [
    StoryParams("aquarium", "shuffle", "shaker", "calm", "Mina", "girl", "Toby", "boy", "mother", 0),
    StoryParams("aquarium", "shuffle", "bell", "tap", "Pia", "girl", "Nico", "boy", "father", 0),
    StoryParams("aquarium", "shuffle", "shaker", "calm", "Arlo", "boy", "Mina", "girl", "mother", 1),
]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    kit: str
    response: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    helper: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for rid, resp in RESPONSES.items():
                if mystery_at_risk(setting, mystery) and resp.sense >= SENSE_MIN:
                    combos.append((sid, mid, rid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-style story for a young child that includes the words "aquarium" and "shuffle".',
        f"Tell a quest story where {f['child1'].id} and {f['child2'].id} search for a treasure at the aquarium, hear a shuffle, and solve the mystery with help.",
        f'Write a gentle mystery story with sound effects and a quest, where a strange shuffle is explained by a simple cause.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, helper = f["child1"], f["child2"], f["helper"]
    return [
        ("Who is the story about?", f"It is about {a.id} and {b.id}, who turned the aquarium visit into a pirate quest. {helper.label_word.capitalize()} helped them solve the mystery."),
        ("What strange sound did they hear?", f"They heard a shuffle sound near the seesaw, and it made the aquarium feel mysterious. The sound mattered because it pointed to a hidden cause."),
        ("What solved the mystery?", f"The ribbon and toy key were freed, so the strange shuffle had a simple explanation. Once that was fixed, the room became calm again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an aquarium?", "An aquarium is a place where people can look at fish swimming in water behind glass."),
        ("What is a seesaw?", "A seesaw is a playground board that goes up and down when children sit on both ends."),
        ("What is a shuffle sound?", "A shuffle sound is a soft sliding or dragging noise, like something moving across the floor."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("shuffle_sound", mid) if "shuffle" in m.tags else asp.fact("sound_mystery", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, R) :- setting(S), mystery(M), response(R), sense(R, X), sense_min(N), X >= N, shuffle_sound(M).
outcome(contained) :- response(R), power(R, P), delay(D), P >= D + 1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: verify smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-style aquarium mystery with a seesaw shuffle and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--kit", choices=SOUND_KITS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError(explain_rejection(SETTINGS.get(args.setting or "aquarium", SETTINGS["aquarium"]),
                                           MYSTERIES.get(args.mystery or "shuffle", MYSTERIES["shuffle"])))
    setting, mystery, response = rng.choice(sorted(combos))
    kit = args.kit or rng.choice(sorted(SOUND_KITS))
    child1, child2 = rng.sample(["Mina", "Toby", "Pia", "Nico", "Arlo", "Lia"], 2)
    child1_gender = rng.choice(["girl", "boy"])
    child2_gender = "boy" if child1_gender == "girl" else "girl"
    helper = rng.choice(["mother", "father"])
    return StoryParams(setting, mystery, kit, response, child1, child1_gender, child2, child2_gender, helper, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], SOUND_KITS[params.kit],
                 RESPONSES[params.response], params.child1, params.child1_gender,
                 params.child2, params.child2_gender, params.helper, params.delay)
    return StorySample(params=params, story=world.render(),
                       prompts=generation_prompts(world),
                       story_qa=[QAItem(q, a) for q, a in story_qa(world)],
                       world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
                       world=world)


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
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
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
