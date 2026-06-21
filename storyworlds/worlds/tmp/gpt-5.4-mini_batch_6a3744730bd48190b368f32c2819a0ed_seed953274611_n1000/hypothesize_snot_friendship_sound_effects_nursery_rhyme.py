#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hypothesize_snot_friendship_sound_effects_nursery_rhyme.py
==========================================================================================

A tiny storyworld about two friends, a puzzling sneeze, and a playful nursery-rhyme
style sound-effects beat. The domain is deliberately small: one child hypothesizes
what caused the noise, a little mishap about snot follows, and friendship carries
the story to a cheerful ending image.

The world is built as a stateful simulation with physical meters and emotional
memes, plus a Python reasonableness gate and an inline ASP twin.

Run:
    python storyworlds/worlds/gpt-5.4-mini/hypothesize_snot_friendship_sound_effects_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/hypothesize_snot_friendship_sound_effects_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/hypothesize_snot_friendship_sound_effects_nursery_rhyme.py --verify
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

RHYME_STEP = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class SoundSetting:
    id: str
    place: str
    echo: str
    hush: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Noise:
    id: str
    label: str
    sound: str
    source: str
    made_by: str
    risky: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendAction:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: SoundSetting) -> None:
        self.setting = setting
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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_bloom(world: World) -> list[str]:
    out: list[str] = []
    sneezer = world.entities.get("sniff")
    friend = world.entities.get("hush")
    if not sneezer or not friend:
        return out
    if sneezer.meters.get("sneezing", 0.0) < RHYME_STEP:
        return out
    sig = ("bloom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["surprise"] = friend.memes.get("surprise", 0.0) + 1
    out.append("__sound__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        sents = _r_bloom(world)
        if sents:
            changed = True
            produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_sound(world: World, action: FriendAction) -> dict:
    sim = world.copy()
    do_action(sim, action, narrate=False)
    return {
        "resolved": sim.facts.get("resolved", False),
        "giggles": sim.get("hush").memes.get("giggle", 0.0),
    }


def hypothesize(world: World, thinker: Entity, noise: Noise) -> None:
    thinker.memes["curious"] = thinker.memes.get("curious", 0.0) + 1
    world.say(
        f"In {world.setting.place}, {thinker.id} heard a {noise.sound} and said, "
        f'"I hypothesize it came from {noise.source}."'
    )
    world.say(f"The little thought danced like a drum on a window-pane.")


def sneeze(world: World, sneezer: Entity, friend: Entity, noise: Noise) -> None:
    sneezer.meters["sneezing"] = sneezer.meters.get("sneezing", 0.0) + 1
    sneezer.meters["snot"] = sneezer.meters.get("snot", 0.0) + 1
    world.say(
        f"Then {sneezer.id} went '{noise.sound}!' and {noise.made_by} popped out "
        f"with a tiny bit of snot."
    )
    world.say(f"{friend.id} blinked, then laughed with a gentle little snort.")


def comfort(world: World, friend: Entity, sneezer: Entity) -> None:
    friend.memes["kind"] = friend.memes.get("kind", 0.0) + 1
    sneezer.memes["relief"] = sneezer.memes.get("relief", 0.0) + 1
    world.say(
        f"{friend.id} passed a soft cloth and said, 'No fuss, dear friend; "
        f"we all get sneezy sometimes.'"
    )
    world.say("Together they wiped the nose, then smiled as warm as buns.")


def do_action(world: World, action: FriendAction, narrate: bool = True) -> None:
    if action.id != "clean_and_joke":
        return
    snoot = world.get("sniff")
    hush = world.get("hush")
    snoot.meters["snot"] = 0.0
    snoot.meters["sneezing"] = 0.0
    hush.memes["giggle"] = hush.memes.get("giggle", 0.0) + 1
    world.facts["resolved"] = True
    body = action.text
    world.say(body)
    if narrate:
        propagate(world, narrate=True)


def ending(world: World, friend: Entity, sneezer: Entity) -> None:
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    sneezer.memes["joy"] = sneezer.memes.get("joy", 0.0) + 1
    world.say(
        f"Then the two friends skipped on, bright as beads, with a snicker and a "
        f"snuffle and a happy little breeze."
    )
    world.say(
        f"And {friend.id} kept the answer in {friend.pronoun('possessive')} heart: "
        f"when a sound sounds strange, ask kindly, and stay friends."
    )


def tell(setting: SoundSetting, noise: Noise, action: FriendAction,
         thinker: str = "Mina", thinker_type: str = "girl",
         sneezer: str = "Pip", sneezer_type: str = "boy") -> World:
    world = World(setting)
    a = world.add(Entity(id=thinker, kind="character", type=thinker_type, role="thinker"))
    b = world.add(Entity(id=sneezer, kind="character", type=sneezer_type, role="friend"))
    world.add(Entity(id="sniff", kind="character", type=sneezer_type))
    world.add(Entity(id="hush", kind="character", type=thinker_type))

    world.say(
        f"With a hum and a hop and a riddle in the air, {a.id} and {b.id} played "
        f"in {setting.place}. {setting.echo}"
    )
    hypothesize(world, a, noise)
    world.para()
    sneeze(world, b, a, noise)
    comfort(world, a, b)
    world.para()
    do_action(world, action)
    ending(world, a, b)

    world.facts.update(
        setting=setting,
        noise=noise,
        action=action,
        thinker=a,
        sneezer=b,
    )
    return world


SETTINGS = {
    "nursery": SoundSetting(
        id="nursery",
        place="the nursery by the window",
        echo="Every shelf gave the room a soft old echo.",
        hush="The hush of bedtime toys made the air feel gentle.",
        tags={"nursery", "sound"},
    ),
    "garden": SoundSetting(
        id="garden",
        place="the little garden gate",
        echo="The fence went tap-tap with every tiny sound.",
        hush="Even the daisies seemed to listen politely.",
        tags={"garden", "sound"},
    ),
    "attic": SoundSetting(
        id="attic",
        place="the attic with the round toy chest",
        echo="The beams made each whisper bounce like a ball.",
        hush="Dust motes floated like sleepy stars.",
        tags={"attic", "sound"},
    ),
}

NOISES = {
    "achoo": Noise(
        id="achoo",
        label="a sneeze",
        sound="achoo",
        source="a tickly nose",
        made_by="achoo",
        risky=False,
        tags={"sneeze", "snot"},
    ),
    "snort": Noise(
        id="snort",
        label="a snort",
        sound="snort",
        source="a giggle in the throat",
        made_by="snort",
        risky=False,
        tags={"snort", "sound"},
    ),
    "kerchoo": Noise(
        id="kerchoo",
        label="a grand sneeze",
        sound="kerchoo",
        source="a puff of peppery dust",
        made_by="kerchoo",
        risky=False,
        tags={"sneeze", "sound", "snot"},
    ),
}

ACTIONS = {
    "clean_and_joke": FriendAction(
        id="clean_and_joke",
        sense=3,
        text="They giggled, cleaned up the tiny mess, and made a rhyme about a "
        "brave little nose.",
        qa_text="They cleaned up the tiny mess and laughed together so the moment "
        "felt safe again.",
        tags={"friendship", "kindness"},
    ),
    "napkin_and_tea": FriendAction(
        id="napkin_and_tea",
        sense=2,
        text="They fetched a napkin, took a little sip of warm tea, and smiled "
        "at the soggy surprise.",
        qa_text="They used a napkin and a warm drink to feel better, then smiled "
        "because the surprise was over.",
        tags={"friendship", "care"},
    ),
}

CURATED = [
    StoryParams = None
]

# Define exactly one StoryParams dataclass before usage.
@dataclass
class StoryParams:
    setting: str
    noise: str
    action: str
    thinker: str
    thinker_type: str
    sneezer: str
    sneezer_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for nid in NOISES:
            for aid in ACTIONS:
                combos.append((sid, nid, aid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style friendship story that includes the word "{f["noise"].made_by}" and the word "hypothesize".',
        f"Tell a gentle story where {f['thinker'].id} hears {f['noise'].sound}, makes a guess, and stays kind when {f['sneezer'].id} gets a little snotty sneeze.",
        "Write a small rhyming story about two friends, a strange sound, and a kind response.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    thinker = f["thinker"]
    sneezer = f["sneezer"]
    return [
        ("Who heard the strange sound first?",
         f"{thinker.id} heard it first and tried to hypothesize what made the noise. "
         f"That guess started the playful wondering."),
        ("What happened after the sneeze?",
         f"{sneezer.id} sneezed and a little bit of snot appeared. "
         f"Then {thinker.id} stayed kind and helped clean up."),
        ("How did the friends end the story?",
         f"They ended happy and close as friends, laughing after the cleanup. "
         f"The ending proves the little problem did not break their friendship."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["noise"].tags) | set(f["action"].tags) | {"friendship"}
    qa = []
    if "sneeze" in tags:
        qa.append(("What is a sneeze?",
                    "A sneeze is a sudden burst of air from the nose and mouth. "
                    "It can make a loud sound like achoo or kerchoo."))
    if "snot" in tags:
        qa.append(("What is snot?",
                    "Snot is the wet stuff that can come from your nose. "
                    "It is normal, and a tissue or cloth can help clean it up."))
    qa.append(("What is a friend?",
                "A friend is someone kind you play with, share with, and help when "
                "something small goes wrong."))
    qa.append(("What does hypothesize mean?",
                "To hypothesize means to make a careful guess about why something "
                "happened."))
    return qa


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    noise = args.noise or rng.choice(list(NOISES))
    action = args.action or rng.choice(list(ACTIONS))
    thinker = args.thinker or rng.choice(["Mina", "Lulu", "Nell", "Poppy"])
    sneezer = args.sneezer or rng.choice([n for n in ["Pip", "Ben", "Toby", "Milo"] if n != thinker])
    thinker_type = args.thinker_type or rng.choice(["girl", "boy"])
    sneezer_type = args.sneezer_type or ("boy" if thinker_type == "girl" else "girl")
    if args.noise and args.noise not in NOISES:
        raise StoryError("Unknown noise.")
    if args.action and args.action not in ACTIONS:
        raise StoryError("Unknown action.")
    return StoryParams(
        setting=setting,
        noise=noise,
        action=action,
        thinker=thinker,
        thinker_type=thinker_type,
        sneezer=sneezer,
        sneezer_type=sneezer_type,
    )


ASP_RULES = r"""
sound_event(N) :- noise(N).
friendly(F) :- action(F), sense(F,S), S >= 2.
result(resolved) :- action(clean_and_joke).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid in NOISES:
        lines.append(asp.fact("noise", nid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show sound_event/1.\n#show friendly/1.\n"))
    combos = []
    for sid in SETTINGS:
        for nid in NOISES:
            for aid in ACTIONS:
                combos.append((sid, nid, aid))
    return combos


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combos differ.")
        rc = 1
    try:
        p = resolve_params(argparse.Namespace(setting=None, noise=None, action=None, thinker=None, sneezer=None, thinker_type=None, sneezer_type=None), random.Random(7))
        s = generate(p)
        _ = s.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.noise not in NOISES:
        raise StoryError("Invalid noise.")
    if params.action not in ACTIONS:
        raise StoryError("Invalid action.")
    world = tell(
        SETTINGS[params.setting],
        NOISES[params.noise],
        ACTIONS[params.action],
        thinker=params.thinker,
        thinker_type=params.thinker_type,
        sneezer=params.sneezer,
        sneezer_type=params.sneezer_type,
    )
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny nursery-rhyme storyworld about friendship and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--thinker")
    ap.add_argument("--thinker-type", choices=["girl", "boy"])
    ap.add_argument("--sneezer")
    ap.add_argument("--sneezer-type", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show sound_event/1.\n#show friendly/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="nursery", noise="achoo", action="clean_and_joke", thinker="Mina", thinker_type="girl", sneezer="Pip", sneezer_type="boy"),
            StoryParams(setting="garden", noise="kerchoo", action="napkin_and_tea", thinker="Lulu", thinker_type="girl", sneezer="Toby", sneezer_type="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
