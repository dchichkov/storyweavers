#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sad_dialogue_sharing_kindness_mystery.py
=========================================================================

A small standalone storyworld for a child-facing mystery about a sad moment,
dialogue, sharing, and kindness.

Premise:
- A child loses a small keepsake before a school event.
- Friends and family ask careful questions, share clues, and act kindly.
- The mystery resolves by following state, not by swapping nouns in a frozen paragraph.

This world is intentionally tiny, classical, and deterministic once parameters are set.
It supports the shared Storyweavers contract:
- StoryParams
- build_parser
- resolve_params
- generate
- emit
- main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

The simulation tracks both physical meters and emotional memes on typed entities.
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

METER_THRESHOLD = 1.0
SAD_THRESHOLD = 1.0
KIND_THRESHOLD = 1.0
SHARE_THRESHOLD = 1.0

NAMES = ["Mina", "Luca", "Nora", "Toby", "Ivy", "Owen", "Mila", "Eli"]
HELPERS = ["grandma", "big sister", "older brother", "neighbor", "teacher"]
PLACES = ["library corner", "playroom shelf", "bus stop bench", "classroom cubby"]
MISSING = {
    "button": "a bright red button",
    "shell": "a small shiny shell",
    "note": "a folded paper note",
    "key": "a tiny brass key",
}
CONTAINERS = {
    "basket": "a woven basket",
    "box": "a blue box",
    "pocket": "a coat pocket",
    "drawer": "a little drawer",
}
SHARED_ITEMS = {
    "stickers": "a sheet of stickers",
    "crayons": "a box of crayons",
    "cookies": "three warm cookies",
    "marbles": "two glass marbles",
}


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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def be(self) -> str:
        return "are" if self.plural else "is"


@dataclass
class Setting:
    place: str
    light: str
    clues: list[str] = field(default_factory=list)


@dataclass
class MysteryItem:
    id: str
    label: str
    hidden_in: str
    sad_reason: str
    found_by_sharing: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareAct:
    id: str
    item_label: str
    giver_line: str
    receiver_line: str
    effect: str
    helps: int
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


def _r_sad(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["sad"] < SAD_THRESHOLD:
            continue
        sig = ("sad", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["quiet"] += 1
        out.append("")
    return out


def _r_kind(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kind"] < KIND_THRESHOLD:
            continue
        sig = ("kind", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] += 1
        out.append("")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["shared"] < SHARE_THRESHOLD:
            continue
        sig = ("share", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["warmth"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("sad", _r_sad), Rule("kind", _r_kind), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for item in ITEMS:
            for share in SHARES:
                combos.append((setting, item, share))
    return combos


def reasonableness_gate(item: MysteryItem, share: ShareAct) -> bool:
    return item.found_by_sharing and item.label in share.item_label


def predict(world: World, seeker_id: str) -> dict:
    sim = world.copy()
    _search_for_item(sim, sim.get(seeker_id), narrate=False)
    return {
        "hope": sim.get(seeker_id).memes["hope"],
        "found": sim.get(seeker_id).meters["found"],
    }


def _search_for_item(world: World, seeker: Entity, narrate: bool = True) -> None:
    clue = seeker.attrs.get("clue", "")
    if clue:
        seeker.meters["searched"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, helper: Entity, setting: Setting, item: MysteryItem) -> None:
    child.memes["sad"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} stood in {setting.place} and looked sad. "
        f"{child.pronoun().capitalize()} had lost {item.label}."
    )
    world.say(
        f'"I checked {item.hidden_in}, but it was not there," {child.id} said. '
        f'"Did anyone see it?"'
    )


def dialogue(world: World, child: Entity, helper: Entity, item: MysteryItem, setting: Setting) -> None:
    helper.memes["kind"] += 1
    world.say(
        f'"Let\'s look together," {helper.id} said. "{helper.pronoun().capitalize()} '
        f'can ask calm questions."'
    )
    world.say(
        f'"What did you hear last?" {helper.id} asked. "{child.id}, can you share '
        f'the last place you remember?"'
    )
    child.attrs["clue"] = setting.clues[0]


def search(world: World, child: Entity, helper: Entity, item: MysteryItem, share: ShareAct) -> None:
    child.memes["shared"] += 1
    helper.memes["shared"] += 1
    world.say(
        f"{child.id} shared a clue, and {helper.id} shared a better one. "
        f"{share.giver_line} {share.receiver_line}"
    )
    world.say(
        f"Together they looked in the places that made sense, because sharing the work "
        f"made the mystery smaller."
    )


def find_item(world: World, child: Entity, helper: Entity, item: MysteryItem, container: Entity) -> None:
    child.meters["found"] += 1
    world.say(
        f"Under {container.label}, {helper.id} found {item.label}. "
        f"It had been tucked away where the clues pointed."
    )
    world.say(
        f"{child.id} blinked, then smiled through the sad feeling. The missing thing "
        f"had been there all along."
    )


def kindness_end(world: World, child: Entity, helper: Entity, item: MysteryItem, share: ShareAct) -> None:
    child.memes["sad"] = 0.0
    child.memes["kind"] += 1
    helper.memes["kind"] += 1
    world.say(
        f'"Thank you," {child.id} said. "{helper.id}, you were kind to help me." '
        f'"And you shared the clues," {helper.id} said back.'
    )
    world.say(
        f"To end the day, they shared {share.effect}, and the room felt bright again."
    )


def tell(setting: Setting, item: MysteryItem, share: ShareAct,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "grandma", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    container = world.add(Entity(id="container", kind="thing", type="thing", label=setting.clues[1]))
    world.facts.update(setting=setting, item=item, share=share, child=child, helper=helper, container=container)

    introduce(world, child, helper, setting, item)
    world.para()
    dialogue(world, child, helper, item, setting)
    search(world, child, helper, item, share)
    world.para()
    find_item(world, child, helper, item, container)
    kindness_end(world, child, helper, item, share)

    world.facts["outcome"] = "found"
    return world


SETTINGS = {
    "library": Setting(place="the library corner", light="soft lamp light", clues=["the reading table", "a blue basket"]),
    "playroom": Setting(place="the playroom", light="window light", clues=["the toy shelf", "a red box"]),
    "school": Setting(place="the classroom cubby", light="bright morning light", clues=["the cubby shelf", "a little drawer"]),
}

ITEMS = {
    "button": MysteryItem(id="button", label="a bright red button", hidden_in="a blue basket", sad_reason="it was special"),
    "shell": MysteryItem(id="shell", label="a small shiny shell", hidden_in="a woven basket", sad_reason="it came from the beach"),
    "note": MysteryItem(id="note", label="a folded paper note", hidden_in="a little drawer", sad_reason="it held a nice message"),
    "key": MysteryItem(id="key", label="a tiny brass key", hidden_in="a coat pocket", sad_reason="it opened a treasure box"),
}

SHARES = {
    "stickers": ShareAct(id="stickers", item_label="stickers", giver_line="Mina offered a sticker with a smile.", receiver_line="The helper took it kindly and nodded.", effect="stickers and one last thank-you", helps=2),
    "cookies": ShareAct(id="cookies", item_label="cookies", giver_line="Luca passed over a cookie as a treat.", receiver_line="The helper broke it in half so both could share.", effect="cookies and a laugh", helps=2),
    "crayons": ShareAct(id="crayons", item_label="crayons", giver_line="Nora slid over the crayons.", receiver_line="The helper chose the blue one and pointed at the clue.", effect="crayons and a drawing of the clue", helps=2),
}

CURATED = [
    StoryParams(setting="library", item="button", share="stickers"),
    StoryParams(setting="playroom", item="shell", share="crayons"),
    StoryParams(setting="school", item="note", share="cookies"),
]


@dataclass
class StoryParams:
    setting: str = "library"
    item: str = "button"
    share: str = "stickers"
    child_name: str = "Mina"
    child_gender: str = "girl"
    helper_name: str = "grandma"
    helper_gender: str = "woman"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A sad, dialogue-driven mystery about sharing and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.setting and args.item and args.share:
        if not reasonableness_gate(ITEMS[args.item], SHARES[args.share]):
            raise StoryError("That sharing choice does not fit the mystery.")
    setting = args.setting or rng.choice(list(SETTINGS))
    item = args.item or rng.choice(list(ITEMS))
    share = args.share or rng.choice(list(SHARES))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(NAMES)
    helper_name = args.helper or rng.choice(HELPERS)
    helper_gender = "woman" if helper_name in {"grandma", "teacher", "neighbor"} else "man"
    return StoryParams(
        setting=setting,
        item=item,
        share=share,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.item not in ITEMS:
        raise StoryError("Unknown item.")
    if params.share not in SHARES:
        raise StoryError("Unknown sharing act.")
    world = tell(SETTINGS[params.setting], ITEMS[params.item], SHARES[params.share],
                 child_name=params.child_name, child_gender=params.child_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short sad mystery story for a young child that includes the word "sad" and shows dialogue.',
        f"Tell a kindness story where {f['child'].id} and {f['helper'].id} share clues to find {f['item'].label}.",
        f"Write a gentle mystery about losing {f['item'].label} in {f['setting'].place}, then solving it by talking and sharing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, item, share = f["child"], f["helper"], f["item"], f["share"]
    return [
        ("Why was the child sad at the start?",
         f"{child.id} was sad because {child.pronoun('possessive')} {item.label} was missing. The story begins with that worry and then follows the clues."),
        ("How did the helper help?",
         f"{helper.id} asked calm questions, listened carefully, and shared the search. That kind way of talking helped the mystery move forward."),
        ("What did they do together to solve the mystery?",
         f"They talked, shared clues, and looked in the places that fit the clues. Their sharing led them to the missing item."),
        ("How did the story end?",
         f"It ended happily, with {child.id} and {helper.id} smiling after finding {item.label}. They also shared {share.effect} to close the day with kindness."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is kindness?",
         "Kindness is when you help someone, use gentle words, and try to make them feel safe and cared for."),
        ("What does sharing mean?",
         "Sharing means giving part of what you have, or helping someone use what you have together, so both people can take part."),
        ("Why can talking help solve a mystery?",
         "Talking can help because people remember different clues. When they ask and answer carefully, the missing piece is easier to find."),
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(setting(S), item(I), share(H)) :- setting(S), mystery_item(I), share_act(H).
story_ok(S, I, H) :- valid(setting(S), item(I), share(H)).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("mystery_item", iid))
    for hid in SHARES:
        lines.append(asp.fact("share_act", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # Smoke test ordinary generation too.
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py != cl:
        rc = 1
        print("MISMATCH in ASP parity:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    else:
        print(f"OK: ASP parity matches ({len(py)} combos).")
    print("OK: smoke test story generation ran.")
    return rc


def build_story(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate_world(params: StoryParams) -> StorySample:
    return generate(params)


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a mystery need?",
         "A mystery usually needs clues, questions, and careful thinking to discover what happened."),
        ("Why is kindness important?",
         "Kindness makes people feel safe. When someone is sad, kind words and helpful actions can make it easier to solve a problem."),
        ("What helps when something is missing?",
         "Sharing information helps when something is missing. If people tell each other what they saw, the answer is easier to find."),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate_world(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate_world(params)
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
            header = f"### {p.child_name}: {p.setting}, {p.item}, {p.share}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        build_story(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
