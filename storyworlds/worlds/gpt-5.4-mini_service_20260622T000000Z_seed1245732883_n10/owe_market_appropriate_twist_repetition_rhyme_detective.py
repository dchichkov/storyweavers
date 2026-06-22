#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T000000Z_seed1245732883_n10/owe_market_appropriate_twist_repetition_rhyme_detective.py
==============================================================================================================================

A standalone storyworld in a tiny detective-style market domain.

Premise:
- A child detective goes to a market to solve a small mystery.
- A seller may owe a payment or apology.
- The detective must choose an appropriate clue or trade.
- A twist reveals the truth.
- Repetition and rhyme shape the narration in a child-facing way.

This file is self-contained apart from the shared result containers in
storyworlds/results.py and the optional ASP helper in storyworlds/asp.py.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

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
    light: str
    sounds: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    owes: bool = False
    appropriate: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    seller: str
    seller_gender: str
    clue: str
    item: str
    response: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "market": Setting(id="market", place="the busy market", light="sunny stalls", sounds="the hum of haggling",
                      tags={"market"}),
    "night_market": Setting(id="night_market", place="the lantern market", light="glowing lanterns", sounds="soft drum taps",
                            tags={"market"}),
}

CLUES = {
    "receipt": Clue(id="receipt", label="receipt", phrase="a crumpled receipt", reveals="the stall with the missing coin",
                    tags={"clue", "receipt"}),
    "rhyme_note": Clue(id="rhyme_note", label="rhyme note", phrase="a little rhyme note", reveals="who the seller had met",
                       tags={"clue", "rhyme"}),
    "sock_tag": Clue(id="sock_tag", label="sock tag", phrase="a sock tag with a scribble", reveals="the exact basket to check",
                     tags={"clue"}),
}

ITEMS = {
    "apple": Item(id="apple", label="apple", phrase="a bright red apple", owes=True, appropriate=True, tags={"apple", "appropriate"}),
    "pin": Item(id="pin", label="pin", phrase="a tiny brass pin", owes=False, appropriate=False, tags={"pin"}),
    "coin": Item(id="coin", label="coin", phrase="a shiny coin", owes=True, appropriate=True, tags={"coin", "owe"}),
}

RESPONSES = {
    "ask_gently": Response(id="ask_gently", sense=3, text="asked the seller a gentle question and listened carefully", fail="asked too quickly and got only a shrug",
                           qa_text="asked the seller a gentle question and listened carefully", tags={"question"}),
    "return_item": Response(id="return_item", sense=3, text="returned the right item to the right stall", fail="returned the wrong item to the wrong stall",
                            qa_text="returned the right item to the right stall", tags={"return"}),
    "pay_debt": Response(id="pay_debt", sense=2, text="paid back what was owed and thanked the seller", fail="paid the wrong stall and made the mix-up worse",
                         qa_text="paid back what was owed and thanked the seller", tags={"owe"}),
    "shout": Response(id="shout", sense=1, text="shouted at the market and scared everyone", fail="shouted at the market and scared everyone",
                      qa_text="shouted at the market", tags={"bad"}),
}

NAMES_GIRL = ["Lena", "Maya", "Nora", "Ivy", "Zoe", "Ada"]
NAMES_BOY = ["Theo", "Milo", "Finn", "Owen", "Eli", "Jack"]


def _new_entity(eid: str, kind: str, type_: str, label: str = "", role: str = "", tags: Optional[set[str]] = None) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, role=role,
                  attrs={}, meters={"mood": 0.0, "truth": 0.0, "debt": 0.0},
                  memes={"curiosity": 0.0, "worry": 0.0, "relief": 0.0},
                  tags=set(tags or []))


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b} in the market light, clues in sight, all felt right."


def repeated_line(word: str) -> str:
    return f"{word.capitalize()}, {word}, the little case grew wise."


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for iid, item in ITEMS.items():
                if item.appropriate and item.owes:
                    for rid, resp in RESPONSES.items():
                        if resp.sense >= 2:
                            combos.append((sid, cid, iid, rid))
    return combos


def reasonableness_check(setting: Setting, clue: Clue, item: Item, response: Response) -> bool:
    return setting.id in SETTINGS and clue.id in CLUES and item.id in ITEMS and response.sense >= 2 and item.appropriate and item.owes


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective market storyworld with owe, market, appropriate, twist, repetition, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--seller")
    ap.add_argument("--seller-gender", choices=["girl", "boy"])
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
              and (args.clue is None or c[1] == args.clue)
              and (args.item is None or c[2] == args.item)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, item, response = rng.choice(sorted(combos))
    det_gender = args.detective_gender or rng.choice(["girl", "boy"])
    help_gender = args.helper_gender or ("boy" if det_gender == "girl" else "girl")
    sell_gender = args.seller_gender or rng.choice(["girl", "boy"])
    detective = args.detective or choose_name(rng, det_gender)
    helper = args.helper or choose_name(rng, help_gender)
    seller = args.seller or choose_name(rng, sell_gender)
    return StoryParams(setting=setting, detective=detective, detective_gender=det_gender,
                       helper=helper, helper_gender=help_gender, seller=seller, seller_gender=sell_gender,
                       clue=clue, item=item, response=response)


def valid_story(params: StoryParams) -> bool:
    try:
        return reasonableness_check(SETTINGS[params.setting], CLUES[params.clue], ITEMS[params.item], RESPONSES[params.response])
    except KeyError:
        return False


def tell(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError("Invalid story parameters.")
    world = World()
    detective = world.add(_new_entity("detective", "character", params.detective_gender, params.detective, "detective"))
    helper = world.add(_new_entity("helper", "character", params.helper_gender, params.helper, "helper"))
    seller = world.add(_new_entity("seller", "character", params.seller_gender, params.seller, "seller"))
    setting = world.add(Entity(id="setting", kind="place", type="place", label=SETTINGS[params.setting].place,
                               attrs={}, meters={"quiet": 0.0, "hints": 0.0}, memes={"mystery": 0.0}, tags=SETTINGS[params.setting].tags))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=CLUES[params.clue].label, attrs={}, meters={"found": 0.0}, memes={"meaning": 0.0}, tags=CLUES[params.clue].tags))
    item = world.add(Entity(id="item", kind="thing", type="item", label=ITEMS[params.item].label, attrs={}, meters={"owed": 0.0}, memes={"need": 0.0}, tags=ITEMS[params.item].tags))
    response = world.add(Entity(id="response", kind="thing", type="response", label=RESPONSES[params.response].id, attrs={}, meters={"good": 0.0}, memes={"sense": 0.0}, tags=RESPONSES[params.response].tags))
    world.facts.update(params=params, setting=SETTINGS[params.setting], clue_cfg=CLUES[params.clue], item_cfg=ITEMS[params.item], response_cfg=RESPONSES[params.response],
                       detective=detective, helper=helper, seller=seller, clue=clue, item=item, response=response)

    detective.memes["curiosity"] = 2
    helper.memes["curiosity"] = 1
    seller.meters["debt"] = 1.0 if ITEMS[params.item].owes else 0.0
    seller.memes["worry"] = 1.0 if ITEMS[params.item].owes else 0.0

    world.say(f"{detective.id} and {helper.id} went to {SETTINGS[params.setting].place}.")
    world.say(f"The {SETTINGS[params.setting].id.replace('_', ' ')} had {SETTINGS[params.setting].sounds}, and {SETTINGS[params.setting].light} glowed around them.")
    world.say(f"{detective.id} was a detective who loved a market mystery, and {helper.id} helped with every clue.")
    world.say(f"At the stall, {seller.id} looked worried, because somebody might {('owe' if ITEMS[params.item].owes else 'not owe')} a little payment.")
    world.para()
    world.say(f"{detective.id} noticed {CLUES[params.clue].phrase}.")
    world.say(repeated_line("Look"))
    world.say(repeated_line("Clue"))
    world.say(f"It was an {('appropriate' if ITEMS[params.item].appropriate else 'odd')} clue for the case.")
    world.say(f"{helper.id} whispered a rhyme: \"Find the line, then read the sign.\"")
    world.para()
    twist = ITEMS[params.item].reveals if ITEMS[params.item].owes else "the truth was hidden in plain sight"
    world.say(f"{detective.id} thought the missing thing was one story, but the twist was another: {twist}.")
    world.say(f"{detective.id} asked the most {RESPONSES[params.response].id.replace('_', ' ')} question and used the right move.")
    if params.response == "pay_debt":
        world.say(f"{RESPONSES[params.response].text.capitalize()}.")
    else:
        world.say(f"{RESPONSES[params.response].text.capitalize()}.")
    world.say(f"{seller.id} smiled, and the market case was solved.")
    world.para()
    world.say(f"{detective.id} returned with {CLUES[params.clue].reveals}, and the stall was calm again.")
    world.say(f"{helper.id} said, \"No fuss, no rush, just the right clue.\"")
    world.say(rhyme_line(detective.id, helper.id))
    world.say(f"That was the appropriate end: the owed little mix-up was paid, and the market felt bright.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a young child that includes the words "owe", "market", and "appropriate".',
        f"Tell a market mystery story where {f['detective'].id} and {f['helper'].id} solve a small case with a twist.",
        f"Write a story with repetition and rhyme about a child detective at the market who learns what is appropriate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, h, s = f["detective"], f["helper"], f["seller"]
    setting, clue_cfg, item_cfg = f["setting"], f["clue_cfg"], f["item_cfg"]
    return [
        QAItem(
            question=f"Who solved the market mystery?",
            answer=f"{d.id} solved it with help from {h.id}. They looked carefully, followed the clue, and found the right answer at the market."
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {item_cfg.reveals}. That changed what {d.id} thought at first and helped the case make sense."
        ),
        QAItem(
            question=f"Why was the clue appropriate?",
            answer=f"It was appropriate because it fit the market case and pointed toward the truth. It helped the detective choose the right next step instead of guessing."
        ),
        QAItem(
            question=f"Did someone owe something in the story?",
            answer=f"Yes. The story made it clear that a small payment or mix-up was owed, and {s.id} was worried until the right thing happened."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem("What is a detective?", "A detective is someone who looks for clues and tries to solve a mystery. Detectives pay attention to little details."),
        QAItem("What is a market?", "A market is a place where people buy and sell things. There are stalls, voices, and lots of small choices."),
        QAItem("What does appropriate mean?", "Appropriate means right for the situation. An appropriate choice fits the problem and helps instead of making it worse."),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        parts.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(parts)


ASP_RULES = r"""
setting(market).
setting(night_market).
clue(receipt).
clue(rhyme_note).
clue(sock_tag).
item(apple).
item(pin).
item(coin).
response(ask_gently).
response(return_item).
response(pay_debt).
sense(ask_gently,3).
sense(return_item,3).
sense(pay_debt,2).
appropriate(apple).
appropriate(coin).
owes(apple).
owes(coin).
valid(S,C,I,R) :- setting(S), clue(C), item(I), response(R), appropriate(I), owes(I), sense(R,N), N >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        if ITEMS[iid].appropriate:
            lines.append(asp.fact("appropriate", iid))
        if ITEMS[iid].owes:
            lines.append(asp.fact("owes", iid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("python-only:", sorted(py - ac))
        print("asp-only:", sorted(ac - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, item=None, response=None, detective=None, detective_gender=None, helper=None, helper_gender=None, seller=None, seller_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: smoke test story generation works.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(setting="market", detective="Lena", detective_gender="girl", helper="Theo", helper_gender="boy", seller="Mina", seller_gender="girl", clue="receipt", item="apple", response="ask_gently"),
    StoryParams(setting="night_market", detective="Owen", detective_gender="boy", helper="Ivy", helper_gender="girl", seller="Nora", seller_gender="girl", clue="rhyme_note", item="coin", response="pay_debt"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
