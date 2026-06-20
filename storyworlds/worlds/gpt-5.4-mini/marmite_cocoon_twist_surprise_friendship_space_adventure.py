#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/marmite_cocoon_twist_surprise_friendship_space_adventure.py
===========================================================================================

A standalone tiny storyworld built from the seed words **marmite** and **cocoon**,
with the narrative instruments **Twist**, **Surprise**, and **Friendship**, in a
space-adventure style.

The domain is a small rescue-and-repair mission on a moon base:
- a child astronaut is excited to open a strange cocoon-like pod,
- the pod hides a surprise friend,
- a sticky marmite mishap threatens the mission,
- a clever twist turns the problem into teamwork,
- and the ending proves the friendship has grown.

This script follows the Storyweavers contract:
- typed entities with meters and memes,
- causal world state driving prose,
- three QA sets grounded in world state,
- Python validity checks plus an inline ASP twin,
- support for --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


@dataclass
class Setting:
    id: str
    place: str
    view: str
    action: str
    tone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    role: str
    can_open: bool = False
    sticky: bool = False
    fragile: bool = False
    emits_surprise: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistMove:
    id: str
    label: str
    power: int
    text: str
    success: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendAid:
    id: str
    label: str
    power: int
    text: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "moonbase": Setting(
        "moonbase",
        "the moon base",
        "A glass dome looked out over silver dust and a sky full of stars.",
        "The control room waited beside a hatch that opened toward the dark crater field.",
        "The station felt quiet, bright, and a little lonely.",
        {"space", "moon", "base"},
    ),
    "orbital-garden": Setting(
        "orbital-garden",
        "the orbital garden",
        "Tiny planters floated under clear panels while stars drifted outside.",
        "A narrow tunnel led from the garden to the repair bay.",
        "The station smelled like leaves, metal, and warm lights.",
        {"space", "garden"},
    ),
}

OBJECTS = {
    "marmite": ObjectCfg(
        "marmite", "a jar of marmite", "sticky spread", sticky=True, fragile=False, tags={"marmite", "sticky"}
    ),
    "cocoon": ObjectCfg(
        "cocoon", "a glowing cocoon pod", "mystery pod", can_open=True, emits_surprise=True, tags={"cocoon", "pod"}
    ),
    "crate": ObjectCfg(
        "crate", "a supply crate", "supply crate", fragile=False, tags={"crate"}
    ),
    "shell": ObjectCfg(
        "shell", "a repair shell", "repair shell", can_open=True, fragile=True, tags={"shell"}
    ),
}

TWISTS = {
    "flip-pan": TwistMove(
        "flip-pan",
        "flip the tray",
        2,
        "They tilted the tray and turned the mess upside down",
        "the sticky spill slid into a neat little blob instead of drifting everywhere",
        {"twist", "cleanup"},
    ),
    "swap-cover": TwistMove(
        "swap-cover",
        "swap the cover",
        3,
        "They swapped the cover and tucked the sticky jar inside a spare shell",
        "the jar stayed safe and the cocoon pod could open without getting smeared",
        {"twist", "cover"},
    ),
    "slow-spin": TwistMove(
        "slow-spin",
        "slow spin",
        1,
        "They gave the tray a careful slow spin",
        "the sticky drop moved to the edge where it could be wiped away",
        {"twist", "gentle"},
    ),
}

FRIENDSHIPS = {
    "helper-friend": FriendAid(
        "helper-friend",
        "helpful friend",
        2,
        "The friend held the flashlight steady and pointed out a safe path",
        {"friendship", "helper"},
    ),
    "shared-fix": FriendAid(
        "shared-fix",
        "shared fix",
        3,
        "The friend passed over a clean cloth and held the pod lid with both hands",
        {"friendship", "teamwork"},
    ),
    "brave-cheer": FriendAid(
        "brave-cheer",
        "brave cheer",
        1,
        "The friend cheered softly so nobody panicked",
        {"friendship", "calm"},
    ),
}

KID_NAMES = ["Nova", "Pip", "Milo", "Luna", "Zuri", "Arlo", "Iris", "Kai"]
GROWNUP_NAMES = ["Captain Mira", "Engineer Sol"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for o in OBJECTS:
            for t in TWISTS:
                for f in FRIENDSHIPS:
                    if combo_ok(s, o, t, f):
                        combos.append((s, o, t, f))
    return combos


def combo_ok(setting_id: str, object_id: str, twist_id: str, friend_id: str) -> bool:
    obj = OBJECTS[object_id]
    twist = TWISTS[twist_id]
    friend = FRIENDSHIPS[friend_id]
    return obj.emits_surprise or obj.can_open or obj.sticky or (twist.power + friend.power >= 3)


@dataclass
class StoryParams:
    setting: str
    object: str
    twist: str
    friendship: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    adult: str
    seed: Optional[int] = None


class StoryWorld(World):
    pass


def _rule_sticky_spill(world: World) -> list[str]:
    out = []
    jar = world.entities.get("marmite_obj")
    if not jar or jar.meters["opened"] < THRESHOLD:
        return out
    sig = ("spill", jar.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jar.meters["sticky"] += 1
    world.get("deck").meters["mess"] += 1
    world.get("hero").memes["surprise"] += 1
    out.append("__spill__")
    return out


def _rule_friendship_boost(world: World) -> list[str]:
    out = []
    if world.get("friend").memes["help"] < THRESHOLD:
        return out
    sig = ("boost", "friend")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["courage"] += 1
    world.get("friend").memes["bond"] += 1
    out.append("__bond__")
    return out


CAUSAL_RULES = [Rule("sticky_spill", "physical", _rule_sticky_spill), Rule("friendship_boost", "social", _rule_friendship_boost)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def predict_open(world: World, object_id: str) -> dict:
    sim = world.copy()
    sim.get(object_id).meters["opened"] += 1
    propagate(sim, narrate=False)
    return {"mess": sim.get("deck").meters["mess"], "surprise": sim.get("hero").memes["surprise"]}


def needs_twist(obj: ObjectCfg) -> bool:
    return obj.sticky or obj.emits_surprise or obj.can_open


def strong_enough(twist: TwistMove, friend: FriendAid) -> bool:
    return twist.power + friend.power >= 3


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(KID_NAMES)


def tell(setting: Setting, obj: ObjectCfg, twist: TwistMove, friend: FriendAid,
         hero_name: str = "Nova", hero_gender: str = "girl",
         friend_name: str = "Pip", friend_gender: str = "boy",
         adult_name: str = "Captain Mira") -> World:
    world = StoryWorld()
    hero = world.add(Entity("hero", "character", hero_gender, role="hero", traits=["curious"]))
    hero.id = hero_name
    friend_ent = world.add(Entity("friend", "character", friend_gender, role="friend", traits=["kind"]))
    friend_ent.id = friend_name
    adult = world.add(Entity("adult", "character", "adult", role="adult"))
    adult.id = adult_name
    deck = world.add(Entity("deck", "thing", "deck"))
    jar = world.add(Entity("marmite_obj", "thing", "marmite", label=obj.label, role=obj.role))
    pod = world.add(Entity("pod", "thing", "cocoon", label="the cocoon pod", role="mystery"))
    hero.memes["wonder"] += 1
    hero.memes["friendship"] += 1
    friend_ent.memes["friendship"] += 1
    world.say(f"On {setting.place}, {hero_name} and {friend_name} drifted through {setting.view.lower()} for their next space adventure.")
    world.say(f"They found {obj.label} beside {pod.label}, and the pod looked like it was waiting for a secret to wake up.")
    world.para()
    world.say(f'"Look," said {hero_name}, "maybe {obj.label} belongs in the cocoon pod!"')
    world.say(f"{friend_name} peered closer. The idea felt exciting, but also a little strange.")
    world.say(f"{setting.tone} made the whole place feel like a story about to turn.")
    if obj.emits_surprise:
        world.say(f"Then the pod trembled, and a surprise light blinked inside like a tiny star.")
    world.para()
    world.say(f"But when {hero_name} opened the jar, the {obj.label} slipped onto the deck.")
    hero.meters["opened"] += 1
    jar.meters["opened"] += 1
    propagate(world, narrate=False)
    if world.get("deck").meters["mess"] >= THRESHOLD:
        world.say(f"The marmite made a sticky dot on the floor, and the crew had to stop their rush for a moment.")
    world.say(f"{friend_name} held the light steady and said, 'We can fix this together.'")
    world.get("friend").memes["help"] += 1
    world.get("adult").memes["calm"] += 1
    world.para()
    world.say(f"That was the twist: {twist.text.lower()}. {twist.success.capitalize()}.")
    world.say(f"{friend.text}.")
    world.say(f"{hero_name} and {friend_name} worked shoulder to shoulder, and the sticky spot shrank into a tiny clean patch.")
    world.get("deck").meters["mess"] = 0.0
    world.get("pod").meters["opened"] += 1
    world.para()
    world.say(f"At last, the cocoon pod opened wide, and out floated a small glowing friend who blinked at the two children.")
    world.say(f"{hero_name} smiled. {friend_name} smiled back. On the moon base, friendship felt brighter than any star.")
    hero.memes["joy"] += 1
    friend_ent.memes["joy"] += 1
    world.facts.update(hero=hero, friend=friend_ent, adult=adult, setting=setting, object_cfg=obj, twist=twist, friend_aid=friend, pod=pod, jar=jar, outcome="surprise-friendship")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story for a young child that includes the words "{f["object_cfg"].id}" and "cocoon".',
        f"Tell a story where {f['hero'].id} meets a surprise friend in a cocoon pod and solves a sticky marmite problem with {f['friend'].id}.",
        f"Write a gentle moon-base adventure with a twist, a surprise, and friendship that ends with everyone feeling happy and safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    f = world.facts["friend"]
    obj = world.facts["object_cfg"]
    twist = world.facts["twist"]
    friend_aid = world.facts["friend_aid"]
    ans1 = (
        f"{h.id} and {f.id} were exploring the moon base together. "
        f"They found {obj.label} near the cocoon pod, and that made the adventure feel mysterious."
    )
    ans2 = (
        f"The twist was that the sticky problem became a teamwork problem, not just a worry. "
        f"{twist.success.capitalize()} because {f.id} stayed calm and helped fix it."
    )
    ans3 = (
        f"At the end, the cocoon pod opened and a surprise friend appeared. "
        f"That changed the mood from tense to happy, because friendship made the whole mission feel safe."
    )
    return [
        QAItem("Who was the story about?", ans1),
        QAItem("What was the twist in the story?", ans2),
        QAItem("How did the story end?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is marmite?", "Marmite is a very sticky spread that can make a messy spill if it tips over."),
        QAItem("What is a cocoon?", "A cocoon is a wrapping or pod that hides something inside until it is ready to emerge."),
        QAItem("Why is friendship important on an adventure?", "Friendship helps everyone stay calm, share the work, and solve problems together."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sticky_spill :- opened(marmite_obj), sticky(marmite_obj).
friendship_boost :- help(friend), not calm_failure.
outcome(surprise_friendship) :- opened(pod), friendship_boost.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.sticky:
            lines.append(asp.fact("sticky", oid))
        if o.can_open:
            lines.append(asp.fact("can_open", oid))
        if o.emits_surprise:
            lines.append(asp.fact("emits_surprise", oid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for fid in FRIENDSHIPS:
        lines.append(asp.fact("friendship", fid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    else:
        print(f"OK: ASP and Python combos match ({len(valid_combos())}).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, object=None, twist=None, friendship=None, hero=None, hero_gender=None, friend=None, friend_gender=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as err:
        print(f"ERROR: generate() smoke test failed: {err}")
        rc = 1
    return rc


def explain_rejection() -> str:
    return "(No story: this combination does not give the story enough room for a twist, a surprise, and a friendship fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with marmite, cocoon, twist, surprise, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--friendship", choices=FRIENDSHIPS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.object_:
        combos = [c for c in combos if c[1] == args.object_]
    if args.twist:
        combos = [c for c in combos if c[2] == args.twist]
    if args.friendship:
        combos = [c for c in combos if c[3] == args.friendship]
    if not combos:
        raise StoryError(explain_rejection())
    setting, obj, twist, friendship = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(KID_NAMES)
    friend = args.friend or rng.choice([n for n in KID_NAMES if n != hero])
    adult = args.adult or rng.choice(GROWNUP_NAMES)
    return StoryParams(setting, obj, twist, friendship, hero, hero_gender, friend, friend_gender, adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        OBJECTS[params.object],
        TWISTS[params.twist],
        FRIENDSHIPS[params.friendship],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.adult,
    )
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c} {d}" for a, b, c, d in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("moonbase", "marmite", "flip-pan", "helper-friend", "Nova", "girl", "Pip", "boy", "Captain Mira"),
            StoryParams("orbital-garden", "cocoon", "swap-cover", "shared-fix", "Luna", "girl", "Kai", "boy", "Engineer Sol"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
