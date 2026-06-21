#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/compromise_reconciliation_curiosity_twist_bedtime_story.py
==========================================================================================

A tiny bedtime storyworld about a child, a small disagreement, a curious twist,
and a gentle compromise that brings everyone back together.

The domain is intentionally small: one child, one parent, one sibling or friend,
one bedtime setting, one curious clue, and one soft compromise that resolves the
mood. The story engine uses typed entities with physical meters and emotional
memes, forward-chained causal rules, a reasonableness gate, and a declarative
ASP twin.

The default premise:
- bedtime is near
- one child is curious about a strange little sound or glow
- another character wants to keep the bedtime routine calm
- they compromise on one gentle check together
- the twist reveals something friendly
- reconciliation follows, and the story ends on a warm bedtime image
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
    scene: str
    bedtime_word: str
    quiet_place: str


@dataclass
class Curiosity:
    id: str
    trigger: str
    clue: str
    check: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Compromise:
    id: str
    offer: str
    action: str
    ending: str
    sense: int = 3
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    reveal: str
    friendly: bool = True
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["curiosity"] >= THRESHOLD and "worry" not in world.fired:
        world.fired.add(("worry",))
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["softened"] >= THRESHOLD and helper.memes["softened"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["love"] += 1
        helper.memes["love"] += 1
        child.memes["worry"] = 0.0
        helper.memes["worry"] = 0.0
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("reconcile", _r_reconcile)]


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


def valid_compromises() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, cur in CURIOSITIES.items():
            for tid, tw in TWISTS.items():
                if cur.friendly and tw.friendly:
                    combos.append((sid, cid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    curiosity: str
    compromise: str
    twist: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld of curiosity, compromise, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--compromise", choices=COMPROMISES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.curiosity and args.twist:
        cur, tw = CURIOSITIES[args.curiosity], TWISTS[args.twist]
        if not (cur.friendly and tw.friendly):
            raise StoryError("This bedtime storyworld keeps the twist gentle and friendly.")
    combos = [c for c in valid_compromises()
              if (args.setting is None or c[0] == args.setting)
              and (args.curiosity is None or c[1] == args.curiosity)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, curiosity, twist = rng.choice(sorted(combos))
    compromise = args.compromise or rng.choice(sorted(COMPROMISES))
    cg = args.child_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or ("boy" if cg == "girl" and rng.random() < 0.5 else "girl")
    child = args.child or _pick_name(rng, cg)
    helper = args.helper or _pick_name(rng, hg, avoid=child)
    return StoryParams(setting=setting, curiosity=curiosity, compromise=compromise, twist=twist,
                       child=child, child_gender=cg, helper=helper, helper_gender=hg)


def _do_curiosity(world: World, child: Entity, curiosity: Curiosity) -> None:
    child.memes["curiosity"] += 1
    world.say(f"At bedtime, {child.id} was still curious about {curiosity.trigger}.")
    world.say(f"{child.pronoun().capitalize()} noticed {curiosity.clue} near {curiosity.check}.")


def _do_compromise(world: World, child: Entity, helper: Entity, compromise: Compromise) -> None:
    child.memes["softened"] += 1
    helper.memes["softened"] += 1
    world.say(f'{helper.id} offered a compromise: "{compromise.offer}."')
    world.say(f'Together, they chose to {compromise.action}.')


def _do_twist(world: World, twist: Twist, child: Entity, helper: Entity) -> None:
    world.say(f"Then came a little twist: {twist.reveal}.")
    child.memes["surprise"] += 1
    helper.memes["surprise"] += 1


def _do_reconciliation(world: World, child: Entity, helper: Entity) -> None:
    world.say(f"{child.id} looked at {helper.id}, and the worry melted away.")
    world.say(f"They smiled at each other again, warm and sleepy.")


def tell(setting: Setting, curiosity: Curiosity, compromise: Compromise, twist: Twist,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Mom", helper_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    lamp = world.add(Entity(id="lamp", type="thing", label="night-light"))
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket"))
    world.facts.update(setting=setting, curiosity=curiosity, compromise=compromise, twist=twist,
                       child=child, helper=helper, lamp=lamp, blanket=blanket)

    world.say(f"{child.id} was getting ready for sleep in {setting.place}.")
    world.say(setting.scene)
    _do_curiosity(world, child, curiosity)
    world.para()
    _do_compromise(world, child, helper, compromise)
    propagate(world, narrate=False)
    world.say(f"They kept the room {setting.bedtime_word} and calm.")
    world.para()
    _do_twist(world, twist, child, helper)
    world.say(f"That was why the little mystery was really {twist.reveal}.")
    child.memes["reconciled"] += 1
    helper.memes["reconciled"] += 1
    _do_reconciliation(world, child, helper)
    world.say(f"At last, {child.id} tucked {blanket.label} under {child.pronoun('possessive')} chin and the {lamp.label} glowed softly.")
    world.say(f"{setting.quiet_place} stayed peaceful, and the night went on like a lullaby.")
    world.facts["outcome"] = "reconciled"
    return world


SETTINGS = {
    "nursery": Setting(id="nursery", place="the nursery", scene="The moonlight made silver shapes on the wall.", bedtime_word="soft", quiet_place="The nursery"),
    "bedroom": Setting(id="bedroom", place="the bedroom", scene="A toy bear sat by the pillow, waiting politely.", bedtime_word="quiet", quiet_place="The bedroom"),
    "attic_room": Setting(id="attic_room", place="the attic room", scene="The slanted ceiling held the night like a cozy hat.", bedtime_word="gentle", quiet_place="The attic room"),
}

CURIOSITIES = {
    "glow": Curiosity(id="glow", trigger="the tiny glow by the curtain", clue="a little gold shimmer", check="the window", reveal="a firefly had wandered in from the garden", tags={"light", "window"}),
    "sound": Curiosity(id="sound", trigger="the tapping sound", clue="a soft tap-tap behind the dresser", check="the dresser", reveal="a friendly mouse was nibbling a crumb", tags={"sound", "dresser"}),
    "shadow": Curiosity(id="shadow", trigger="the shadow near the bed", clue="a round lump under the quilt", check="the quilt", reveal="a sleepy kitten had curled into a ball", tags={"shadow", "bed"}),
}

COMPROMISES = {
    "peek": Compromise(id="peek", offer="we can take one quiet peek together", action="peek once and then come right back to bed", ending="They peeked together and felt braver.", sense=3, tags={"gentle"}),
    "listen": Compromise(id="listen", offer="we can listen for one tiny minute", action="listen for one minute with the lamp low", ending="They listened, and the night answered kindly.", sense=3, tags={"gentle"}),
    "snuggle": Compromise(id="snuggle", offer="we can solve the mystery while snuggling", action="snuggle under the blanket and look together", ending="They snuggled, and the worry turned soft.", sense=3, tags={"gentle"}),
}

TWISTS = {
    "firefly": Twist(id="firefly", reveal="a firefly had wandered in from the garden", friendly=True, tags={"firefly"}),
    "mouse": Twist(id="mouse", reveal="a tiny mouse was visiting for crumbs", friendly=True, tags={"mouse"}),
    "kitten": Twist(id="kitten", reveal="a kitten had climbed up for a nap", friendly=True, tags={"kitten"}),
}

GIRL_NAMES = ["Mia", "Ella", "Nora", "Lily", "Ava", "June", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Noah", "Eli", "Sam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "compromise" and a gentle surprise.',
        f"Tell a cozy story where {f['child'].id} is curious about {f['curiosity'].trigger}, and {f['helper'].id} offers a compromise before the twist is revealed.",
        f"Write a bedtime story about curiosity, compromise, and reconciliation, ending with a sleepy, happy room.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, cur, comp, tw = f["child"], f["helper"], f["curiosity"], f["compromise"], f["twist"]
    return [
        ("Who was the story about?",
         f"It was about {child.id} at bedtime, and {helper.id} stayed close to help. The story followed their feelings as curiosity turned into a calm shared moment."),
        ("What did {0} want to know about?".format(child.id),
         f"{child.id} wanted to know about {cur.trigger}. The clue looked small, but it made {child.id} curious enough to pause before sleep."),
        ("What compromise did they make?",
         f"They agreed to {comp.action}. That let them stay calm and check the mystery together instead of arguing about it."),
        ("What was the twist?",
         f"The twist was that {tw.reveal}. It turned the mystery into something friendly, which helped them reconcile."),
        ("How did the story end?",
         f"{child.id} and {helper.id} were warm, happy, and reconciled by the end. They fell asleep after the mystery became a gentle bedtime moment."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a compromise?",
         "A compromise is when people choose a middle way that helps everyone feel okay. It is a kind way to solve a small disagreement."),
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to learn more about something. It often helps children ask questions and notice little clues."),
        ("What is reconciliation?",
         "Reconciliation means people become friendly again after a disagreement. They listen, forgive, and return to being at peace."),
        ("What is a twist in a story?",
         "A twist is a surprise that changes what you thought was happening. It can make the story feel fresh and interesting."),
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


CURATED = [
    StoryParams(setting="nursery", curiosity="glow", compromise="peek", twist="firefly",
                child="Mia", child_gender="girl", helper="Mom", helper_gender="girl"),
    StoryParams(setting="bedroom", curiosity="sound", compromise="listen", twist="mouse",
                child="Leo", child_gender="boy", helper="Dad", helper_gender="boy"),
    StoryParams(setting="attic_room", curiosity="shadow", compromise="snuggle", twist="kitten",
                child="Nora", child_gender="girl", helper="Mom", helper_gender="girl"),
]


def explain_choice(cur: Curiosity, tw: Twist) -> str:
    return "This bedtime storyworld only uses gentle twists and calm curiosities."


def outcome_of(params: StoryParams) -> str:
    return "reconciled"


ASP_RULES = r"""
curious(child) :- curiosity(_,_,_,_,_).
softened(child) :- compromise(_,_,_,_,_).
reconciled(child, helper) :- softened(child), softened(helper).
twist_friendly(T) :- twist(T), friendly(T).
valid(S, C, T) :- setting(S), curiosity(C), twist(T), twist_friendly(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CURIOSITIES.items():
        lines.append(asp.fact("curiosity", cid))
        if c.friendly:
            lines.append(asp.fact("friendly", cid))
    for cid in COMPROMISES:
        lines.append(asp.fact("compromise", cid))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        if t.friendly:
            lines.append(asp.fact("friendly", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_compromises()):
        print(f"OK: ASP gate matches valid_compromises() ({len(valid_compromises())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, curiosity=None, compromise=None, twist=None, child=None, child_gender=None, helper=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.curiosity not in CURIOSITIES or params.compromise not in COMPROMISES or params.twist not in TWISTS:
        raise StoryError("Unknown story parameters.")
    world = tell(SETTINGS[params.setting], CURIOSITIES[params.curiosity], COMPROMISES[params.compromise], TWISTS[params.twist],
                 params.child, params.child_gender, params.helper, params.helper_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for s, c, t in asp_valid_combos():
            print(f"  {s} {c} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
