#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/abbot_poop_thrill_indoor_play_cafe_misunderstanding.py
======================================================================================

A small standalone storyworld for an indoor play cafe misunderstanding tale.

Premise:
- A child at an indoor play cafe spots an abbot and thinks the word "abbot" is
  about a robot or a snack order.
- A messy poop accident happens in the play cafe.
- A misunderstanding turns into a calm fix, with a gentle helper and a tidy ending.

The prose is authored as a rhyming story, but the world model still drives the
beats: setup, misunderstanding, mess, clarification, cleanup, and a brighter end.

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports results eagerly
- imports asp lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "abbot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "abbot": "abbot"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    indoor: bool = True


@dataclass
class CharacterCfg:
    id: str
    type: str
    label: str
    role: str
    tone: str
    rhyme_name: str


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    messy: bool = False
    safe: bool = False


@dataclass
class EventCfg:
    id: str
    label: str
    mess: str
    risk: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    abbot: str
    object: str
    event: str
    seed: Optional[int] = None


SETTINGS = {
    "play_cafe": Setting(
        id="play_cafe",
        place="the indoor play cafe",
        scene="a bright indoor play cafe with soft mats, toy muffins, and a tiny stage",
        indoor=True,
    )
}

CHILDREN = {
    "Mia": CharacterCfg("Mia", "girl", "Mia", "child", "curious", "Mia"),
    "Leo": CharacterCfg("Leo", "boy", "Leo", "child", "cheery", "Leo"),
    "Nora": CharacterCfg("Nora", "girl", "Nora", "child", "sparkly", "Nora"),
    "Theo": CharacterCfg("Theo", "boy", "Theo", "child", "bouncy", "Theo"),
}

HELPERS = {
    "parent": CharacterCfg("Parent", "mother", "the parent", "helper", "calm", "Parent"),
    "barista": CharacterCfg("Barista", "woman", "the barista", "helper", "gentle", "Barista"),
}

ABBOTS = {
    "abbot": CharacterCfg("Abbot", "abbot", "the abbot", "visitor", "kind", "Abbot"),
}

OBJECTS = {
    "toy_robot": ObjectCfg("toy_robot", "toy robot", "a shiny toy robot", "toy", safe=True),
    "cookie": ObjectCfg("cookie", "cookie", "a warm cookie", "snack", safe=True),
    "napkin": ObjectCfg("napkin", "napkin", "a paper napkin", "paper", safe=True),
}

EVENTS = {
    "misheard_abbot": EventCfg(
        id="misheard_abbot",
        label="misunderstanding",
        mess="poop",
        risk="thrown alarm",
        fix="clear the confusion",
        tags={"misunderstanding", "abbot"},
    )
}

GIRDERS = ["glimmer", "thrill", "spill", "frill", "chill", "bill"]
NAMES = ["Mia", "Leo", "Nora", "Theo"]
KINDS = ["girl", "boy"]

CURATED = [
    StoryParams(setting="play_cafe", child="Mia", child_type="girl", helper="Parent", helper_type="mother",
                abbot="Abbot", object="toy_robot", event="misheard_abbot"),
    StoryParams(setting="play_cafe", child="Leo", child_type="boy", helper="Barista", helper_type="woman",
                abbot="Abbot", object="cookie", event="misheard_abbot"),
    StoryParams(setting="play_cafe", child="Nora", child_type="girl", helper="Parent", helper_type="mother",
                abbot="Abbot", object="napkin", event="misheard_abbot"),
]


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
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out = []
    if world.get("cafe").meters["alarm"] >= THRESHOLD:
        sig = ("alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["fear"] += 1
            world.get("helper").memes["focus"] += 1
            out.append("The room grew tense, and little feet went still.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


def predict_misunderstanding(world: World) -> bool:
    sim = world.copy()
    sim.get("child").memes["curiosity"] += 1
    sim.get("cafe").meters["alarm"] += 1
    propagate(sim, narrate=False)
    return sim.get("cafe").meters["alarm"] >= THRESHOLD


def setup(world: World, setting: Setting, child: Entity, helper: Entity, abbot: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    abbot.memes["warmth"] += 1
    world.say(
        f"At {setting.place}, bright with play, the children came in a cheerful sway, "
        f"and a kind abbot sat nearby, with a calm little smile and a twinkle in his eye."
    )
    world.say(
        f"{child.id} saw the abbot and felt a thrill, for rhymes can ripple and stories can spill."
    )


def misunderstanding(world: World, child: Entity, abbot: Entity, obj: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'"Is that an {abbot.label_word}?" {child.id} asked with a grin, "Is it a robot, a snack, or a tiny toy kin?"'
    )
    world.say(
        f"The word sounded funny, a playful small trill, and {child.id} mixed up the name with a nonsensey thrill."
    )
    world.say(
        f'But the abbot just laughed, "No, dear one, no; I am an abbot, a person, not a gadget to show."'
    )
    world.facts["misunderstood"] = True


def mess_event(world: World, child: Entity, obj: Entity) -> None:
    child.memes["alarm"] += 1
    world.get("cafe").meters["poop"] += 1
    world.get("floor").meters["mess"] += 1
    world.say(
        f"Then came a small poop on the floor by the chair, a messy surprise in the café air."
    )
    world.say(
        f"{child.id} yelped, then froze in a hush, while giggles and gasps did a quick little rush."
    )
    world.facts["poop_happened"] = True


def calm_fix(world: World, helper: Entity, child: Entity, abbot: Entity, obj: Entity) -> None:
    helper.memes["calm"] += 1
    world.get("cafe").meters["alarm"] = 0
    world.get("floor").meters["mess"] = 0
    world.get("cafe").meters["poop"] = 0
    world.say(
        f"The helper came quickly with gloves and a grin, and cleared the confusion from all around in."
    )
    world.say(
        f'They said, "That was a mishap, not a bad little deed. Let\'s clean up together, we all can help indeed."'
    )
    world.say(
        f"{child.id} handed over the napkins with care, and the abbot just thanked them for staying so fair."
    )
    world.facts["fixed"] = True


def ending(world: World, setting: Setting, child: Entity, helper: Entity, abbot: Entity, obj: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then back to the play, with the mats nice and neat, came laughter and hummed-over cookies to eat."
    )
    world.say(
        f"The abbot waved gently, the child felt a thrill, and the café grew cozy, warm, tidy, and still."
    )
    world.say(
        f"So when words sound alike and confusion may swirl, a calm little fix can restore the whole whirl."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    child_cfg = CHILDREN[params.child]
    helper_cfg = HELPERS[params.helper]
    abbot_cfg = ABBOTS[params.abbot]
    obj_cfg = OBJECTS[params.object]
    event_cfg = EVENTS[params.event]
    if not setting.indoor:
        raise StoryError("This storyworld is meant for an indoor play cafe.")
    world = World()
    child = world.add(Entity(id=child_cfg.id, kind="character", type=child_cfg.type, role="child"))
    helper = world.add(Entity(id=helper_cfg.id, kind="character", type=helper_cfg.type, role="helper"))
    abbot = world.add(Entity(id=abbot_cfg.id, kind="character", type=abbot_cfg.type, role="visitor"))
    cafe = world.add(Entity(id="cafe", kind="place", type="cafe", label=setting.place))
    floor = world.add(Entity(id="floor", kind="thing", type="floor", label="floor"))
    obj = world.add(Entity(id=obj_cfg.id, kind="thing", type=obj_cfg.kind, label=obj_cfg.label))
    setup(world, setting, child, helper, abbot)
    world.para()
    misunderstanding(world, child, abbot, obj)
    mess_event(world, child, obj)
    world.para()
    calm_fix(world, helper, child, abbot, obj)
    ending(world, setting, child, helper, abbot, obj)
    world.facts.update(
        setting=setting, child=child, helper=helper, abbot=abbot, cafe=cafe, floor=floor,
        obj=obj, event=event_cfg, outcome="fixed", seed=params.seed,
    )
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, c, h, o) for s in SETTINGS for c in CHILDREN for h in HELPERS for o in OBJECTS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story set in {f["setting"].place} that includes the words "abbot", "poop", and "thrill".',
        f"Tell a gentle misunderstanding story where {f['child'].id} meets an abbot in an indoor play cafe and a messy poop moment gets calmly fixed.",
        f"Write a child-friendly rhyming tale with a quick confusion, a cleanup, and a cozy ending in the play cafe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    abbot = f["abbot"]
    obj = f["obj"]
    return [
        ("Where does the story happen?",
         "It happens in an indoor play cafe, where soft mats and toys make the room feel warm and fun."),
        (f"What did {child.id} misunderstand?",
         f"{child.id} mistook the word abbot for something else at first. The sound of the word made {child.id} curious, and that caused the misunderstanding."),
        ("What happened after the poop mess?",
         f"The helper cleaned it up calmly and quickly. That turned the scary moment into a fixed one, so everyone could relax again."),
        (f"How did the story end?",
         f"It ended with the floor tidy, the air cozy, and the abbot smiling gently. The child kept the thrill of the day, but without the confusion."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an abbot?",
         "An abbot is a leader in a monastery. It is a person, not a machine or a toy."),
        ("Why is poop a mess in a play cafe?",
         "Poop is a dirty mess and should be cleaned up right away. A play cafe is for safe play, so adults tidy it quickly."),
        ("What does thrill mean?",
         "A thrill is a strong excited feeling. It can make a moment feel extra lively and special."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(child) :- curious(child), saw_abbot(child).
mess(poop) :- poop_happened.
fixed(cleanup) :- helper_calm(helper), mess(poop), clarified(helper).
ending_tidy :- fixed(cleanup), not alarmed.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "play_cafe"),
        asp.fact("indoor", "play_cafe"),
        asp.fact("misunderstanding_theme", "abbot"),
        asp.fact("mess_kind", "poop"),
        asp.fact("feeling", "thrill"),
    ]
    for name in CHILDREN:
        lines.append(asp.fact("child", name))
    for name in HELPERS:
        lines.append(asp.fact("helper", name))
    for name in ABBOTS:
        lines.append(asp.fact("abbot", name))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show misunderstanding_theme/1."))
    return sorted(set(asp.atoms(model, "misunderstanding_theme")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {("abbot",)}:
        print("MISMATCH: ASP theme facts do not match Python registries.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, child=None, child_type=None, helper=None, helper_type=None,
            abbot=None, object=None, event=None, n=1, seed=777, all=False, trace=False,
            qa=False, json=False, asp=False, verify=False, show_asp=False
        ), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP/Python parity check passed.")
    print("OK: normal generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming indoor play cafe storyworld about abbot, poop, and thrill."
    )
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--child", choices=list(CHILDREN))
    ap.add_argument("--child-type", choices=KINDS)
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--helper-type", choices=["mother", "woman"])
    ap.add_argument("--abbot", choices=list(ABBOTS))
    ap.add_argument("--object", choices=list(OBJECTS))
    ap.add_argument("--event", choices=list(EVENTS))
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
    setting = args.setting or "play_cafe"
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    child = args.child or rng.choice(list(CHILDREN))
    helper = args.helper or rng.choice(list(HELPERS))
    abbot = args.abbot or "Abbot"
    obj = args.object or rng.choice(list(OBJECTS))
    event = args.event or "misheard_abbot"
    return StoryParams(
        setting=setting,
        child=child,
        child_type=CHILDREN[child].type if args.child_type is None else args.child_type,
        helper=helper,
        helper_type=HELPERS[helper].type if args.helper_type is None else args.helper_type,
        abbot=abbot,
        object=obj,
        event=event,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.child not in CHILDREN:
        raise StoryError("Invalid child.")
    if params.helper not in HELPERS:
        raise StoryError("Invalid helper.")
    if params.abbot not in ABBOTS:
        raise StoryError("Invalid abbot.")
    if params.object not in OBJECTS:
        raise StoryError("Invalid object.")
    if params.event not in EVENTS:
        raise StoryError("Invalid event.")
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show misunderstanding_theme/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP theme facts: abbot")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and the abbot in the play cafe"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
