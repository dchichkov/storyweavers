#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/heather_sound_effects_bravery_pirate_tale.py
=============================================================================

A standalone storyworld for a tiny pirate-tale domain: a child named Heather,
some noisy pretend pirate action, a scary sound, and a brave choice that turns
the trouble into a cheerful ending.

The world is built around:
- sound effects as physical meters in the scene,
- bravery as an emotional meme that can rise or fall,
- a pretend pirate setting with a dark spot, a noisy clue, and a safe, brave fix.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/heather_sound_effects_bravery_pirate_tale.py
    python storyworlds/worlds/gpt-5.4-mini/heather_sound_effects_bravery_pirate_tale.py --qa
    python storyworlds/worlds/gpt-5.4-mini/heather_sound_effects_bravery_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/heather_sound_effects_bravery_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
BRAVERY_START = 2.0
BRAVERY_GOOD = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "danger": 0.0, "safety": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "fear": 0.0, "joy": 0.0}

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
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    ship_name: str
    dark_spot: str
    afford_sound: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SoundSource:
    id: str
    label: str
    effect: str
    source: str
    scary: bool = False
    loudness: int = 1
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class BraveAction:
    id: str
    label: str
    method: str
    result: str
    safety: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
@dataclass
class StoryParams:
    setting: str
    sound: str
    action: str
    hero_name: str
    sidekick_name: str
    hero_gender: str
    sidekick_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "cove": Setting("cove", "a moonlit cove", "the Starfish", "the cave under the dock"),
    "deck": Setting("deck", "the deck of a tiny ship", "the Little Gull", "the dark space below the sail"),
    "beach": Setting("beach", "a windy beach", "the Shell Ship", "the shadow behind a sand hill"),
}

SOUNDS = {
    "creak": SoundSource("creak", "a creaky plank", "creeeak", "the old mast", scary=True, loudness=2, tags={"sound", "pirate"}),
    "whistle": SoundSource("whistle", "the wind whistle", "whooooo", "the rigging", scary=True, loudness=2, tags={"sound", "wind"}),
    "drip": SoundSource("drip", "a dripping rope", "drip-drip", "a wet rope", scary=False, loudness=1, tags={"sound", "water"}),
    "drum": SoundSource("drum", "a little drum", "boom-boom", "Heather's toy drum", scary=False, loudness=1, tags={"sound", "music"}),
}

ACTIONS = {
    "call_back": BraveAction("call_back", "call back in a brave voice", "call out", "the fear was smaller once the voices joined in", 1, tags={"brave", "sound"}),
    "shine_lantern": BraveAction("shine_lantern", "shine the lantern", "lift the lantern high", "the dark spot became only a shadow", 2, tags={"brave", "light"}),
    "investigate": BraveAction("investigate", "follow the sound", "walk closer and peek", "the mystery turned into a silly little surprise", 3, tags={"brave", "curious"}),
    "tap_rhythm": BraveAction("tap_rhythm", "tap a rhythm", "tap-boom tap-boom", "the strange sound became a game", 2, tags={"brave", "sound"}),
}

GIRL_NAMES = ["Heather", "Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Finn", "Theo", "Noah", "Eli", "Max", "Ben"]


def hazard_at_risk(sound: SoundSource, setting: Setting) -> bool:
    return sound.scary and setting.afford_sound


def action_safe(action: BraveAction) -> bool:
    return action.safety >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for snd in SOUNDS.values():
            for act in ACTIONS.values():
                if hazard_at_risk(snd, setting) and action_safe(act):
                    combos.append((sid, snd.id, act.id))
    return combos


def reasonableness_gate(sound: SoundSource, action: BraveAction, setting: Setting) -> None:
    if not hazard_at_risk(sound, setting):
        raise StoryError("No story: this sound is not scary enough to need bravery in this setting.")
    if not action_safe(action):
        raise StoryError("No story: the chosen brave action is not safe or sensible enough.")


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("scene").meters["danger"] += 1
    hero.memes["fear"] += 1
    out.append("__noise__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["bravery"] < BRAVERY_GOOD:
        return out
    sig = ("brave", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("scene").meters["safety"] += 1
    hero.memes["joy"] += 1
    out.append("__brave__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_noise, _r_bravery):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def act_sound(world: World, sound: SoundSource) -> None:
    world.get("scene").meters["noise"] += sound.loudness
    world.get("hero").meters["noise"] += sound.loudness
    world.get("hero").memes["fear"] += 1
    propagate(world, narrate=False)


def tell_brave_story(world: World, sound: SoundSource, action: BraveAction) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    scene = world.get("scene")

    world.say(
        f"On the deck of {world.setting.ship_name}, {hero.id} and {sidekick.id} played pirate games in "
        f"{world.setting.place}. {hero.id} held a map, and {sidekick.id} held a bright grin."
    )
    world.say(
        f"Then came {sound.effect} from {sound.source}, and the sound seemed to crawl through {world.setting.dark_spot}."
    )
    act_sound(world, sound)

    world.para()
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} swallowed a gulp of worry and listened again. "
        f'"{sound.effect}!" {hero.id} whispered, and {sidekick.id} leaned closer.'
    )

    if hero.memes["bravery"] >= BRAVERY_GOOD or action.id in {"call_back", "shine_lantern", "tap_rhythm"}:
        hero.memes["bravery"] += 2
        world.say(
            f"With a brave breath, {hero.id} chose to {action.method}. "
            f"Their voices and footsteps made a cheerful pirate rhythm: {sound.effect}, {action.method}, {sound.effect}!"
        )
        scene.meters["danger"] = 0.0
        scene.meters["safety"] += 1
        hero.memes["fear"] = 0.0
        hero.memes["joy"] += 2
        world.para()
        world.say(
            f"The scary sound faded into a game, and the dark spot became safe enough to explore. "
            f"{action.result.capitalize()}. In the end, {hero.id} stood a little taller, like a captain with a steady heart."
        )
        outcome = "brave"
    else:
        world.say(
            f"{hero.id} wanted to be brave, but the echo still felt big. "
            f"{sidekick.id} stayed close until the whole crew could laugh together."
        )
        outcome = "soft"

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        setting=world.setting,
        sound=sound,
        action=action,
        outcome=outcome,
        scene=scene,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-tale story for a young child that includes "{f["hero"].id}" and the sound "{f["sound"].effect}".',
        f"Tell a brave pirate story where {f['hero'].id} hears {f['sound'].label} and chooses to be brave.",
        f"Write a story about a child named {f['hero'].id} who uses sound effects and bravery to solve a scary pirate moment.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    sound = f["sound"]
    action = f["action"]
    outcome = f["outcome"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {sidekick.id}, two children playing pirate games on the ship."),
        ("What strange sound did they hear?",
         f"They heard {sound.effect} from {sound.source}. It sounded spooky at first, but it was only a clue in the pirate game."),
        ("What did {0} do to be brave?".format(hero.id),
         f"{hero.id} chose to {action.method}. That brave choice turned the scary moment into something they could handle together."),
    ]
    if outcome == "brave":
        qa.append((
            "How did the story end?",
            f"It ended happily. The strange sound became part of the game, and {hero.id} felt brave and proud at the end."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended gently, with {hero.id} still a little nervous but safer because {sidekick.id} stayed close."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sound = f["sound"]
    action = f["action"]
    out = []
    if "sound" in sound.tags:
        out.append((
            "What is a sound effect?",
            "A sound effect is a special noise that helps tell a story or make a game feel more exciting."
        ))
    if sound.scary:
        out.append((
            "Why can a creaky sound feel scary?",
            "A creaky sound can feel scary because it is sudden and weird, so your imagination fills in the rest."
        ))
    if "brave" in action.tags:
        out.append((
            "What does bravery mean?",
            "Bravery means doing the next helpful thing even when you feel a little scared."
        ))
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(S, P) :- scary(S), setting(P).
safe_action(A) :- action(A), safety(A, N), N >= 1.
valid(P, S, A) :- hazard(S, P), safe_action(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if s.scary:
            lines.append(asp.fact("scary", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("safety", aid, a.safety))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        ok = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:  # noqa: BLE001
        ok = 1
        print(f"SMOKE TEST FAILED: {e}")
    return ok


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with sound effects and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sound is None or c[1] == args.sound)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sound, action = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or "girl"
    sidekick_gender = args.sidekick_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or ("Heather" if hero_gender == "girl" else rng.choice(BOY_NAMES))
    sidekick_name = args.sidekick_name or rng.choice([n for n in (GIRL_NAMES if sidekick_gender == "girl" else BOY_NAMES) if n != hero_name])
    return StoryParams(setting, sound, action, hero_name, sidekick_name, hero_gender, sidekick_gender)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity("hero", kind="character", type=params.hero_gender, label=params.hero_name, role="hero"))
    sidekick = world.add(Entity("sidekick", kind="character", type=params.sidekick_gender, label=params.sidekick_name, role="sidekick"))
    scene = world.add(Entity("scene", kind="thing", type="scene", label=world.setting.place))
    hero.memes["bravery"] = BRAVERY_START
    sound = SOUNDS[params.sound]
    action = ACTIONS[params.action]
    reasonableness_gate(sound, action, world.setting)
    tell_brave_story(world, sound, action)
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


CURATED = [
    StoryParams("cove", "creak", "call_back", "Heather", "Finn", "girl", "boy"),
    StoryParams("deck", "whistle", "shine_lantern", "Heather", "Mia", "girl", "girl"),
    StoryParams("beach", "drum", "tap_rhythm", "Heather", "Theo", "girl", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
